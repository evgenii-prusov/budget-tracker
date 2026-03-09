"""E2E tests for GET /reports/spending endpoint."""

from decimal import Decimal
from datetime import date


def _create_account(client, name, currency="EUR", initial_balance="1000.00", is_savings=False):
    resp = client.post(
        "/accounts/",
        json={
            "name": name,
            "currency": currency,
            "initial_balance": initial_balance,
            "is_savings": is_savings,
        },
    )
    assert resp.status_code == 201
    return resp.json()["account_id"]


def _create_category_hierarchy(client, parent_name, sub_name, category_type="EXPENSE"):
    parent_resp = client.post(
        "/categories/",
        json={"name": parent_name, "category_type": category_type},
    )
    assert parent_resp.status_code == 201
    parent_id = parent_resp.json()["category_id"]

    sub_resp = client.post(
        "/categories/",
        json={"name": sub_name, "category_type": category_type, "parent_id": parent_id},
    )
    assert sub_resp.status_code == 201
    sub_id = sub_resp.json()["category_id"]

    return parent_id, sub_id


def _create_posting(
    client, account_id, amount, posting_date, posting_type="EXPENSE", category_id=None
):
    payload = {
        "account_id": account_id,
        "amount": str(amount),
        "posting_date": posting_date.isoformat()
        if isinstance(posting_date, date)
        else posting_date,
        "posting_type": posting_type,
    }
    if category_id:
        payload["category_id"] = category_id
    resp = client.post("/postings/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def test_unauthorized_returns_401(client_no_auth):
    response = client_no_auth.get(
        "/reports/spending", params={"period": "month", "reference_date": "2026-03-15"}
    )
    assert response.status_code == 401


def test_spending_report_empty(client):
    """No postings → empty rows list."""
    response = client.get(
        "/reports/spending", params={"period": "month", "reference_date": "2026-03-15"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "month"
    assert data["start_date"] == "2026-03-01"
    assert data["end_date"] == "2026-03-31"
    assert data["rows"] == []


def test_spending_report_aggregates_by_parent_category(client):
    """Two subcategories under same parent → single row with summed total."""
    acc_id = _create_account(client, "Agg Test Account")
    parent_id, sub1_id = _create_category_hierarchy(client, "Food Agg", "Groceries Agg")
    sub2_resp = client.post(
        "/categories/",
        json={"name": "Restaurant Agg", "category_type": "EXPENSE", "parent_id": parent_id},
    )
    assert sub2_resp.status_code == 201
    sub2_id = sub2_resp.json()["category_id"]

    _create_posting(client, acc_id, "30.00", date(2026, 3, 10), category_id=sub1_id)
    _create_posting(client, acc_id, "20.00", date(2026, 3, 12), category_id=sub2_id)

    response = client.get(
        "/reports/spending", params={"period": "month", "reference_date": "2026-03-15"}
    )
    assert response.status_code == 200
    rows = response.json()["rows"]

    food_rows = [r for r in rows if r["parent_category_id"] == parent_id]
    assert len(food_rows) == 1
    assert Decimal(food_rows[0]["total"]) == Decimal("50.00")
    assert food_rows[0]["currency"] == "EUR"


def test_spending_report_excludes_savings_accounts_by_default(client):
    """Postings on savings accounts are excluded when exclude_savings=true (default)."""
    savings_id = _create_account(client, "Savings Excl", is_savings=True)
    regular_id = _create_account(client, "Regular Excl")
    parent_id, sub_id = _create_category_hierarchy(client, "Food Excl", "Groceries Excl")

    _create_posting(client, savings_id, "100.00", date(2026, 3, 5), category_id=sub_id)
    _create_posting(client, regular_id, "40.00", date(2026, 3, 5), category_id=sub_id)

    response = client.get(
        "/reports/spending", params={"period": "month", "reference_date": "2026-03-15"}
    )
    assert response.status_code == 200
    rows = response.json()["rows"]

    food_rows = [r for r in rows if r["parent_category_id"] == parent_id]
    assert len(food_rows) == 1
    assert Decimal(food_rows[0]["total"]) == Decimal("40.00")


def test_spending_report_includes_savings_when_false(client):
    """exclude_savings=false includes savings account postings."""
    savings_id = _create_account(client, "Savings Incl", is_savings=True)
    regular_id = _create_account(client, "Regular Incl")
    parent_id, sub_id = _create_category_hierarchy(client, "Food Incl", "Groceries Incl")

    _create_posting(client, savings_id, "100.00", date(2026, 3, 5), category_id=sub_id)
    _create_posting(client, regular_id, "40.00", date(2026, 3, 5), category_id=sub_id)

    response = client.get(
        "/reports/spending",
        params={"period": "month", "reference_date": "2026-03-15", "exclude_savings": "false"},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]

    food_rows = [r for r in rows if r["parent_category_id"] == parent_id]
    assert len(food_rows) == 1
    assert Decimal(food_rows[0]["total"]) == Decimal("140.00")


def test_spending_report_period_month_filters_dates(client):
    """Posting outside the month is excluded."""
    acc_id = _create_account(client, "Date Filter Account")
    parent_id, sub_id = _create_category_hierarchy(client, "Food DateF", "Groceries DateF")

    _create_posting(client, acc_id, "50.00", date(2026, 3, 15), category_id=sub_id)  # inside March
    _create_posting(client, acc_id, "30.00", date(2026, 2, 28), category_id=sub_id)  # outside March

    response = client.get(
        "/reports/spending", params={"period": "month", "reference_date": "2026-03-15"}
    )
    assert response.status_code == 200
    rows = response.json()["rows"]

    food_rows = [r for r in rows if r["parent_category_id"] == parent_id]
    assert len(food_rows) == 1
    assert Decimal(food_rows[0]["total"]) == Decimal("50.00")


def test_spending_report_income_excluded(client):
    """INCOME postings are not counted in spending report."""
    acc_id = _create_account(client, "Income Excl Account")
    parent_id, sub_id = _create_category_hierarchy(client, "Food IncE", "Groceries IncE")
    inc_parent_id, inc_sub_id = _create_category_hierarchy(
        client, "Salary IncE", "Monthly IncE", "INCOME"
    )

    _create_posting(client, acc_id, "50.00", date(2026, 3, 15), category_id=sub_id)
    _create_posting(
        client, acc_id, "2000.00", date(2026, 3, 1), posting_type="INCOME", category_id=inc_sub_id
    )

    response = client.get(
        "/reports/spending", params={"period": "month", "reference_date": "2026-03-15"}
    )
    assert response.status_code == 200
    rows = response.json()["rows"]

    income_rows = [r for r in rows if r["parent_category_id"] == inc_parent_id]
    assert income_rows == []

    food_rows = [r for r in rows if r["parent_category_id"] == parent_id]
    assert len(food_rows) == 1
    assert Decimal(food_rows[0]["total"]) == Decimal("50.00")


def test_spending_report_invalid_period_returns_422(client):
    response = client.get("/reports/spending", params={"period": "quarter"})
    assert response.status_code == 422


def test_spending_report_missing_period_returns_422(client):
    response = client.get("/reports/spending")
    assert response.status_code == 422
