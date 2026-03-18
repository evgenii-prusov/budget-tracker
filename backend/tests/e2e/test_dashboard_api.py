"""E2E tests for dashboard API endpoints."""

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


# ── Income vs Spending ────────────────────────────────────────────


class TestIncomeVsSpendingUnauthorized:
    def test_unauthorized_returns_401(self, client_no_auth):
        response = client_no_auth.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 401


class TestIncomeVsSpendingEmpty:
    def test_income_vs_spending_empty(self, client):
        """No postings → zeros, ratios null."""
        response = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["currency"] == "EUR"
        assert Decimal(data["total_income"]) == Decimal("0")
        assert Decimal(data["total_spending"]) == Decimal("0")
        assert Decimal(data["net_income"]) == Decimal("0")
        assert data["spending_ratio"] is None


class TestIncomeVsSpendingWithData:
    def test_income_vs_spending_with_data(self, client):
        """Create income + expense, verify totals + spending_ratio."""
        acc_id = _create_account(client, "IvS Data Account")
        _, inc_sub_id = _create_category_hierarchy(client, "Salary IvS", "Monthly IvS", "INCOME")
        _, exp_sub_id = _create_category_hierarchy(client, "Food IvS", "Groceries IvS")

        _create_posting(
            client,
            acc_id,
            "2000.00",
            date(2026, 3, 1),
            posting_type="INCOME",
            category_id=inc_sub_id,
        )
        _create_posting(
            client,
            acc_id,
            "500.00",
            date(2026, 3, 10),
            category_id=exp_sub_id,
        )

        response = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_income"]) == Decimal("2000")
        assert Decimal(data["total_spending"]) == Decimal("500")
        assert Decimal(data["net_income"]) == Decimal("1500")
        # spending_ratio = spending / income * 100 = 500/2000 * 100 = 25
        assert Decimal(data["spending_ratio"]) == Decimal("25")


class TestIncomeVsSpendingMissingCurrency:
    def test_missing_currency_returns_422(self, client):
        response = client.get(
            "/dashboard/income-vs-spending",
            params={"reference_date": "2026-03-15"},
        )
        assert response.status_code == 422


# ── Spending by Categories ────────────────────────────────────────


class TestSpendingByCategoriesUnauthorized:
    def test_unauthorized_returns_401(self, client_no_auth):
        response = client_no_auth.get(
            "/dashboard/spending-by-categories",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 401


class TestSpendingByCategoriesFiltersCurrency:
    def test_spending_by_categories_filters_currency(self, client):
        """EUR only when currency=EUR."""
        eur_acc_id = _create_account(client, "SbC EUR Account", currency="EUR")
        usd_acc_id = _create_account(client, "SbC USD Account", currency="USD")
        _, exp_sub_id = _create_category_hierarchy(client, "Food SbC", "Groceries SbC")

        _create_posting(client, eur_acc_id, "100.00", date(2026, 3, 5), category_id=exp_sub_id)
        _create_posting(client, usd_acc_id, "200.00", date(2026, 3, 5), category_id=exp_sub_id)

        response = client.get(
            "/dashboard/spending-by-categories",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 200
        data = response.json()
        # Should only contain EUR rows
        for row in data:
            assert row["currency"] == "EUR"
        totals = sum(Decimal(r["total"]) for r in data)
        assert totals == Decimal("100")


class TestSpendingByCategoriesMissingCurrency:
    def test_missing_currency_returns_422(self, client):
        response = client.get(
            "/dashboard/spending-by-categories",
            params={"reference_date": "2026-03-15"},
        )
        assert response.status_code == 422


# ── Spending Timeline ─────────────────────────────────────────────


class TestSpendingTimelineUnauthorized:
    def test_unauthorized_returns_401(self, client_no_auth):
        response = client_no_auth.get(
            "/dashboard/spending-timeline",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 401


class TestSpendingTimelineCumulative:
    def test_spending_timeline_cumulative(self, client):
        """Verify daily spending accumulates correctly."""
        acc_id = _create_account(client, "Timeline Acc")
        _create_posting(client, acc_id, "30.00", date(2026, 3, 5))
        _create_posting(client, acc_id, "20.00", date(2026, 3, 10))

        response = client.get(
            "/dashboard/spending-timeline",
            params={"currency": "EUR", "reference_date": "2026-03-15"},
        )
        assert response.status_code == 200
        data = response.json()
        current = data["current_period"]
        assert len(current) == 2
        assert Decimal(current[0]["daily_total"]) == Decimal("30")
        assert Decimal(current[0]["cumulative_total"]) == Decimal("30")
        assert Decimal(current[1]["daily_total"]) == Decimal("20")
        assert Decimal(current[1]["cumulative_total"]) == Decimal("50")


class TestSpendingTimelineProjection:
    def test_spending_timeline_projection(self, client):
        """Verify projected_total is calculated."""
        acc_id = _create_account(client, "Proj Acc")
        _create_posting(client, acc_id, "100.00", date(2026, 3, 10))

        response = client.get(
            "/dashboard/spending-timeline",
            params={"currency": "EUR", "reference_date": "2026-03-10"},
        )
        assert response.status_code == 200
        data = response.json()
        # projected_total = cumulative * days_in_month / day_of_month
        # = 100 * 31 / 10 = 310
        assert data["projected_total"] is not None
        assert Decimal(data["projected_total"]) == Decimal("310")


class TestSpendingTimelineMissingCurrency:
    def test_missing_currency_returns_422(self, client):
        response = client.get(
            "/dashboard/spending-timeline",
            params={"reference_date": "2026-03-15"},
        )
        assert response.status_code == 422


# ── Period parameter ─────────────────────────────────────────────


class TestPeriodParameterValidation:
    def test_invalid_period_returns_422_income_vs_spending(self, client):
        response = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "period": "biweekly"},
        )
        assert response.status_code == 422

    def test_invalid_period_returns_422_spending_by_categories(self, client):
        response = client.get(
            "/dashboard/spending-by-categories",
            params={"currency": "EUR", "period": "biweekly"},
        )
        assert response.status_code == 422

    def test_invalid_period_returns_422_spending_timeline(self, client):
        response = client.get(
            "/dashboard/spending-timeline",
            params={"currency": "EUR", "period": "biweekly"},
        )
        assert response.status_code == 422


class TestPeriodQuarterEndpoints:
    def test_income_vs_spending_quarter(self, client):
        response = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "period": "quarter", "reference_date": "2026-02-15"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == "2026-01-01"
        assert data["end_date"] == "2026-03-31"

    def test_spending_by_categories_quarter(self, client):
        response = client.get(
            "/dashboard/spending-by-categories",
            params={"currency": "EUR", "period": "quarter", "reference_date": "2026-02-15"},
        )
        assert response.status_code == 200

    def test_spending_timeline_quarter(self, client):
        response = client.get(
            "/dashboard/spending-timeline",
            params={"currency": "EUR", "period": "quarter", "reference_date": "2026-02-15"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == "2026-01-01"
        assert data["end_date"] == "2026-03-31"


class TestPeriodYearEndpoints:
    def test_income_vs_spending_year(self, client):
        response = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "period": "year", "reference_date": "2026-06-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == "2026-01-01"
        assert data["end_date"] == "2026-12-31"

    def test_spending_timeline_year(self, client):
        response = client.get(
            "/dashboard/spending-timeline",
            params={"currency": "EUR", "period": "year", "reference_date": "2026-06-01"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == "2026-01-01"
        assert data["end_date"] == "2026-12-31"


class TestPeriodDataScoping:
    def test_jan_posting_visible_in_quarter_not_in_feb_month(self, client):
        """A posting in Jan shows up for period=quarter&ref=Feb but not period=month&ref=Feb."""
        acc_id = _create_account(client, "Period Scope Acc")
        _, sub_id = _create_category_hierarchy(client, "Food PS", "Groceries PS")
        _create_posting(client, acc_id, "75.00", date(2026, 1, 20), category_id=sub_id)

        # Quarter view (Q1) includes Jan
        q_resp = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "period": "quarter", "reference_date": "2026-02-15"},
        )
        assert q_resp.status_code == 200
        assert Decimal(q_resp.json()["total_spending"]) == Decimal("75")

        # Month view (Feb) does NOT include Jan posting
        m_resp = client.get(
            "/dashboard/income-vs-spending",
            params={"currency": "EUR", "period": "month", "reference_date": "2026-02-15"},
        )
        assert m_resp.status_code == 200
        assert Decimal(m_resp.json()["total_spending"]) == Decimal("0")
