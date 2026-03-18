from decimal import Decimal
from tests.constants import JAN_01, JAN_02, JAN_03


def test_unauthorized_returns_401(client_no_auth):
    response = client_no_auth.get("/postings/")
    assert response.status_code == 401


def test_create_posting_expense_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("-50.00")
    assert posting_response["posting_date"] == JAN_01.isoformat()
    assert posting_response["posting_type"] == "EXPENSE"
    assert posting_response["category_id"] == category_id
    assert "posting_id" in posting_response


def test_create_posting_income_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["income_category_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "75.50",
        "posting_date": JAN_02.isoformat(),
        "posting_type": "INCOME",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("75.50")
    assert posting_response["posting_date"] == JAN_02.isoformat()
    assert posting_response["posting_type"] == "INCOME"
    assert posting_response["category_id"] == category_id
    assert "posting_id" in posting_response


def test_create_posting_no_category_success(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "25.00",
        "posting_date": JAN_03.isoformat(),
        "posting_type": "EXPENSE",
        # category_id omitted
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("-25.00")
    assert posting_response["posting_date"] == JAN_03.isoformat()
    assert posting_response["posting_type"] == "EXPENSE"
    assert posting_response["category_id"] is None


def test_create_posting_account_not_found(client, test_data):
    category_id = test_data["category_id"]

    posting_data = {
        "account_id": "non-existent-account-id",
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)
    assert response.status_code == 400
    assert "Account with id 'non-existent-account-id' not found" in response.json()["detail"]


def test_create_posting_category_not_found(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": "non-existent-category-id",
    }

    response = client.post("/postings/", json=posting_data)
    assert response.status_code == 400
    assert "Category with id 'non-existent-category-id' not found" in response.json()["detail"]


def test_create_posting_insufficient_funds(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "150.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": None,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 422
    assert "Insufficient funds in account 'Test Posting Account'" in response.json()["detail"]


def test_get_posting_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["income_category_id"]

    # Create posting
    posting_data = {
        "account_id": account_id,
        "amount": "123.45",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "INCOME",
        "category_id": category_id,
    }
    create_response = client.post("/postings/", json=posting_data)
    assert create_response.status_code == 201
    posting_id = create_response.json()["posting_id"]

    # Get posting
    response = client.get(f"/postings/{posting_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["posting_id"] == posting_id
    assert data["account_id"] == account_id
    assert Decimal(data["amount"]) == Decimal("123.45")
    assert data["posting_date"] == JAN_01.isoformat()
    assert data["posting_type"] == "INCOME"
    assert data["category_id"] == category_id


def test_get_posting_not_found(client):
    response = client.get("/postings/non-existent-id")
    assert response.status_code == 404
    assert "Posting with id 'non-existent-id' not found" in response.json()["detail"]


def test_list_postings_endpoint(client, test_data):
    account_id = test_data["account_id"]

    # Create two postings
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "20.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    # Act
    response = client.get("/postings/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_postings_pagination(client, test_data):
    account_id = test_data["account_id"]

    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "20.00",
            "posting_date": JAN_02.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "30.00",
            "posting_date": JAN_03.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    response = client.get("/postings/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["posting_date"] == JAN_02.isoformat()


def test_create_posting_with_payee_and_description(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "30.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
        "payee": "Grocery Store",
        "description": "Weekly groceries",
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    data = response.json()
    assert data["payee"] == "Grocery Store"
    assert data["description"] == "Weekly groceries"


def test_create_posting_without_payee_description_defaults_null(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "10.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    data = response.json()
    assert data["payee"] is None
    assert data["description"] is None


def test_get_posting_includes_payee_and_description(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "15.00",
        "posting_date": JAN_02.isoformat(),
        "posting_type": "INCOME",
        "payee": "Employer Inc",
        "description": "Bonus payment",
    }

    create_response = client.post("/postings/", json=posting_data)
    assert create_response.status_code == 201
    posting_id = create_response.json()["posting_id"]

    response = client.get(f"/postings/{posting_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["payee"] == "Employer Inc"
    assert data["description"] == "Bonus payment"


def test_list_postings_endpoint_filtered(client, test_data):
    account_id = test_data["account_id"]

    # Create another account
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Another Account",
            "currency": "EUR",
            "initial_balance": "100.00",
        },
    )
    another_account_id = acc_response.json()["account_id"]

    # Create posting in original account
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    # Create posting in another account
    client.post(
        "/postings/",
        json={
            "account_id": another_account_id,
            "amount": "20.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    # Act: Get filtered by account_id
    response = client.get(f"/postings/?account_id={account_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    for posting in data:
        assert posting["account_id"] == account_id


# --- Update (PATCH) posting tests ---


def test_update_posting_amount(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    # Create an expense posting for 50
    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "50.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
            "category_id": category_id,
        },
    )
    assert create_response.status_code == 201
    posting_id = create_response.json()["posting_id"]

    # Update amount from 50 to 30
    response = client.patch(f"/postings/{posting_id}", json={"amount": "30.00"})

    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["amount"]) == Decimal("-30.00")
    assert data["posting_id"] == posting_id


def test_update_posting_date(client, test_data):
    account_id = test_data["account_id"]

    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    posting_id = create_response.json()["posting_id"]

    response = client.patch(f"/postings/{posting_id}", json={"posting_date": JAN_02.isoformat()})

    assert response.status_code == 200
    assert response.json()["posting_date"] == JAN_02.isoformat()


def test_update_posting_category(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
            "category_id": category_id,
        },
    )
    posting_id = create_response.json()["posting_id"]

    # Clear the category
    response = client.patch(f"/postings/{posting_id}", json={"category_id": None})

    assert response.status_code == 200
    assert response.json()["category_id"] is None


def test_update_posting_payee_and_description(client, test_data):
    account_id = test_data["account_id"]

    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    posting_id = create_response.json()["posting_id"]

    response = client.patch(
        f"/postings/{posting_id}",
        json={"payee": "New Payee", "description": "New description"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["payee"] == "New Payee"
    assert data["description"] == "New description"


def test_update_posting_not_found(client):
    response = client.patch("/postings/non-existent-id", json={"amount": "10.00"})
    assert response.status_code == 404


def test_update_posting_insufficient_funds(client, test_data):
    account_id = test_data["account_id"]

    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    posting_id = create_response.json()["posting_id"]

    # Account has initial_balance=100, try to set expense to 200
    response = client.patch(f"/postings/{posting_id}", json={"amount": "200.00"})

    assert response.status_code == 422
    assert "Insufficient funds" in response.json()["detail"]


def test_update_posting_updates_account_balance(client, test_data):
    account_id = test_data["account_id"]

    # Get initial balance
    initial_balance = Decimal(client.get(f"/accounts/{account_id}").json()["balance"])

    # Create expense for 30
    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "30.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    posting_id = create_response.json()["posting_id"]

    balance_after_create = Decimal(client.get(f"/accounts/{account_id}").json()["balance"])
    assert balance_after_create == initial_balance - Decimal("30.00")

    # Update amount to 10
    client.patch(f"/postings/{posting_id}", json={"amount": "10.00"})

    balance_after_update = Decimal(client.get(f"/accounts/{account_id}").json()["balance"])
    assert balance_after_update == initial_balance - Decimal("10.00")


def test_update_posting_type_expense_to_income(client, test_data):
    account_id = test_data["account_id"]

    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    posting_id = create_response.json()["posting_id"]

    # Change type to INCOME (also clear category to avoid type mismatch)
    response = client.patch(
        f"/postings/{posting_id}",
        json={"posting_type": "INCOME", "category_id": None},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["posting_type"] == "INCOME"
    assert Decimal(data["amount"]) == Decimal("10.00")


def test_update_posting_rejects_unknown_fields_only(client, test_data):
    account_id = test_data["account_id"]

    create_response = client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    posting_id = create_response.json()["posting_id"]

    response = client.patch(f"/postings/{posting_id}", json={"foo": "bar"})
    assert response.status_code == 422


def test_delete_posting_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    # Create posting
    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    create_response = client.post("/postings/", json=posting_data)
    assert create_response.status_code == 201
    posting_id = create_response.json()["posting_id"]

    # Verify posting was created
    get_response = client.get(f"/postings/{posting_id}")
    assert get_response.status_code == 200

    # Delete posting
    delete_response = client.delete(f"/postings/{posting_id}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    # Verify posting is deleted
    get_response = client.get(f"/postings/{posting_id}")
    assert get_response.status_code == 404


def test_delete_posting_not_found(client):
    response = client.delete("/postings/non-existent-id")
    assert response.status_code == 404
    assert "Posting with id 'non-existent-id' not found" in response.json()["detail"]


def test_delete_posting_restores_account_balance(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    # Get initial balance
    account_response = client.get(f"/accounts/{account_id}")
    initial_balance = Decimal(account_response.json()["balance"])

    # Create posting
    posting_data = {
        "account_id": account_id,
        "amount": "30.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    create_response = client.post("/postings/", json=posting_data)
    posting_id = create_response.json()["posting_id"]

    # Verify balance changed
    account_after_posting = client.get(f"/accounts/{account_id}")
    balance_after_posting = Decimal(account_after_posting.json()["balance"])
    assert balance_after_posting == initial_balance - Decimal("30.00")

    # Delete posting
    delete_response = client.delete(f"/postings/{posting_id}")
    assert delete_response.status_code == 204

    # Verify balance restored
    account_after_delete = client.get(f"/accounts/{account_id}")
    balance_after_delete = Decimal(account_after_delete.json()["balance"])
    assert balance_after_delete == initial_balance


def test_suggest_payees_endpoint(client, test_data):
    account_id = test_data["account_id"]
    income_category_id = test_data["income_category_id"]

    # Create postings with payees
    for payee in ["Lidl", "Lidl", "Landlord", "Aldi"]:
        client.post(
            "/postings/",
            json={
                "account_id": account_id,
                "amount": "100.00",
                "posting_date": JAN_01.isoformat(),
                "posting_type": "INCOME",
                "category_id": income_category_id,
                "payee": payee,
            },
        )

    response = client.get("/postings/payees", params={"q": "L"})
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    # Lidl has 2 occurrences, Landlord has 1
    assert result[0] == "Lidl"
    assert "Landlord" in result
    assert "Aldi" not in result  # doesn't start with "L"


def test_suggest_payees_requires_query(client):
    response = client.get("/postings/payees")
    assert response.status_code == 422
