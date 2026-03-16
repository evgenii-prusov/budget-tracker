import pytest
from decimal import Decimal


def test_unauthorized_no_header(client_no_auth):
    response = client_no_auth.get("/accounts")
    assert response.status_code == 401


def test_unauthorized_wrong_token(client_no_auth):
    response = client_no_auth.get("/accounts", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401


def test_authorized_valid_token(client):
    response = client.get("/accounts")
    assert response.status_code == 200


def test_docs_accessible_without_auth(client_no_auth):
    """Interactive docs must be reachable without authentication."""
    assert client_no_auth.get("/docs").status_code == 200
    assert client_no_auth.get("/redoc").status_code == 200
    assert client_no_auth.get("/openapi.json").status_code == 200


def test_get_account_success(client):
    # 1. Arrange: Create account via API
    create_response = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    # 2. Act: Make the request
    response = client.get(f"/accounts/{account_id}")

    # 3. Assert: Check status code and account properties
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == account_id
    assert data["name"] == "EUR_1"
    assert data["currency"] == "EUR"
    assert Decimal(data["initial_balance"]) == Decimal(35)


def test_get_account_not_found(client):
    # 1. Arrange: no data in database
    # 2. Act: Make the request
    response = client.get("/accounts/a1")

    # 3. Assert: Check if 404 error code has been returned
    assert response.status_code == 404


def test_get_accounts(client):
    # 1. Arrange: Create account via API
    create_response = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    )
    assert create_response.status_code == 201

    # 2. Act: Make the request
    response = client.get("/accounts")

    # 3. Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "EUR_1"


def test_get_accounts_empty_database(client):
    # 1. Arrange: Empty database (no accounts added)

    # 2. Act: Make the request
    response = client.get("/accounts")

    # 3. Assert: Check the response returns empty list
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_get_accounts_pagination(client):
    client.post(
        "/accounts",
        json={"name": "Account A", "currency": "EUR", "initial_balance": "10"},
    )
    client.post(
        "/accounts",
        json={"name": "Account B", "currency": "EUR", "initial_balance": "20"},
    )
    client.post(
        "/accounts",
        json={"name": "Account C", "currency": "EUR", "initial_balance": "30"},
    )

    response = client.get("/accounts?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Account B"


def test_create_account_duplicate_name(client):
    # 1. Arrange: Create an account via API
    client.post(
        "/accounts",
        json={
            "name": "EUR_1",
            "currency": "EUR",
            "initial_balance": "35",
        },
    )

    # 2. Act: Try to create an account with the same name
    response = client.post(
        "/accounts",
        json={
            "name": "EUR_1",
            "currency": "USD",
            "initial_balance": 100.0,
        },
    )

    # 3. Assert: Check the response
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]
    assert "EUR_1" in data["detail"]


def test_create_account_negative_initial_balance(client):
    # 1. Arrange & Act: Try to create account with negative initial balance
    response = client.post(
        "/accounts",
        json={
            "name": "NegativeAccount",
            "currency": "USD",
            "initial_balance": -100.0,
        },
    )

    # 2. Assert: Check the response
    assert response.status_code == 400
    data = response.json()
    assert "cannot be negative" in data["detail"]
    assert "-100" in data["detail"]


def test_create_account_invalid_currency_returns_400(client):
    response = client.post(
        "/accounts",
        json={
            "name": "Bad Currency",
            "currency": "BITCOIN",
            "initial_balance": "10",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "Invalid currency" in data["detail"]
    assert "BITCOIN" in data["detail"]


@pytest.mark.parametrize(
    "initial_balance, expected_balance",
    [
        ("100.50", "100.50"),  # Two decimal places
        ("0.01", "0.01"),  # Small decimal
        ("123.456789", "123.46"),  # Rounded to 2 decimal places by Numeric(15,2)
        (100, "100"),  # Integer input
        (100.50, "100.50"),  # Float input
    ],
)
def test_create_account_precision_and_types(client, initial_balance, expected_balance):
    # Act
    safe_name = f"Test {initial_balance}".replace(".", "_")
    payload = {
        "name": safe_name,
        "currency": "USD",
        "initial_balance": initial_balance,
    }
    response = client.post("/accounts", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["initial_balance"]) == Decimal(expected_balance)


def test_decimal_precision_persistence_flow(client):
    """
    Verify that decimal precision (2 places) is preserved through a full save-load cycle.
    """
    # Arrange & Act: Create an account with a decimal value
    create_response = client.post(
        "/accounts",
        json={
            "name": "Precision Flow Test",
            "currency": "EUR",
            "initial_balance": "999.99",
        },
    )
    assert create_response.status_code == 201
    created_id = create_response.json()["account_id"]

    # Act: Retrieve all accounts
    get_response = client.get("/accounts")

    # Assert
    assert get_response.status_code == 200
    accounts = get_response.json()
    saved_account = next((a for a in accounts if a["account_id"] == created_id), None)
    assert saved_account is not None, f"Account {created_id} not found"
    assert Decimal(saved_account["initial_balance"]) == Decimal("999.99")


def test_delete_account_success(client):
    """Successfully delete an account with no transfers."""
    # 1. Arrange: Create account via API
    create_response = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    # 2. Act: Delete the account
    response = client.delete(f"/accounts/{account_id}")

    # 3. Assert: Check response and verify deletion
    assert response.status_code == 204

    # Verify account is gone
    get_response = client.get("/accounts")
    assert get_response.status_code == 200
    assert get_response.json() == []


def test_delete_account_with_postings_fails(client):
    """Delete fails when account has postings."""
    # 1. Arrange: Create account, category, and posting via API
    acc = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    ).json()
    parent = client.post(
        "/categories/", json={"name": "Test Parent", "category_type": "INCOME"}
    ).json()
    cat = client.post(
        "/categories/",
        json={"name": "Test Sub", "category_type": "INCOME", "parent_id": parent["category_id"]},
    ).json()
    client.post(
        "/postings/",
        json={
            "account_id": acc["account_id"],
            "amount": "100",
            "posting_date": "2025-01-01",
            "category_id": cat["category_id"],
            "posting_type": "INCOME",
        },
    )

    # 2. Act: Delete the account
    response = client.delete(f"/accounts/{acc['account_id']}")

    # 3. Assert
    assert response.status_code == 409
    assert "has 1 posting" in response.json()["detail"]

    # Verify account still exists
    get_response = client.get("/accounts")
    accounts = get_response.json()
    assert len(accounts) == 1
    assert accounts[0]["account_id"] == acc["account_id"]


def test_delete_account_not_found(client):
    """Attempting to delete non-existent account returns 404."""
    # 1. Arrange: Empty database

    # 2. Act: Try to delete non-existent account
    response = client.delete("/accounts/nonexistent-id")

    # 3. Assert
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]
    assert "nonexistent-id" in data["detail"]


def test_delete_account_with_transfer_returns_409(client):
    """Cannot delete account involved in a transfer."""
    # 1. Arrange: Create two accounts and a transfer via API
    acc1 = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    ).json()
    acc2 = client.post(
        "/accounts",
        json={"name": "RUB_1", "currency": "RUB", "initial_balance": "0"},
    ).json()
    client.post(
        "/transfers/",
        json={
            "source_account_id": acc1["account_id"],
            "dest_account_id": acc2["account_id"],
            "debit_amount": "10",
            "credit_amount": "1000",
            "transfer_date": "2025-01-01",
        },
    )

    # 2. Act: Try to delete source account
    response = client.delete(f"/accounts/{acc1['account_id']}")

    # 3. Assert
    assert response.status_code == 409
    data = response.json()
    assert "Cannot delete" in data["detail"]
    assert "transfer" in data["detail"]

    # Verify account still exists
    get_response = client.get("/accounts")
    assert len(get_response.json()) == 2


def test_delete_account_destination_of_transfer_returns_409(client):
    """Cannot delete account that is destination of a transfer."""
    # 1. Arrange: Create two accounts and a transfer via API
    acc1 = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    ).json()
    acc2 = client.post(
        "/accounts",
        json={"name": "RUB_1", "currency": "RUB", "initial_balance": "0"},
    ).json()
    client.post(
        "/transfers/",
        json={
            "source_account_id": acc1["account_id"],
            "dest_account_id": acc2["account_id"],
            "debit_amount": "10",
            "credit_amount": "1000",
            "transfer_date": "2025-01-01",
        },
    )

    # 2. Act: Try to delete destination account
    response = client.delete(f"/accounts/{acc2['account_id']}")

    # 3. Assert
    assert response.status_code == 409
    assert "Cannot delete" in response.json()["detail"]


def test_delete_account_with_postings_and_transfers_returns_409(client):
    acc1 = client.post(
        "/accounts",
        json={"name": "EUR_Combo", "currency": "EUR", "initial_balance": "35"},
    ).json()
    acc2 = client.post(
        "/accounts",
        json={"name": "RUB_Combo", "currency": "RUB", "initial_balance": "0"},
    ).json()
    parent = client.post(
        "/categories/", json={"name": "Combo Parent", "category_type": "INCOME"}
    ).json()
    cat = client.post(
        "/categories/",
        json={"name": "Combo Sub", "category_type": "INCOME", "parent_id": parent["category_id"]},
    ).json()
    client.post(
        "/postings/",
        json={
            "account_id": acc1["account_id"],
            "amount": "100",
            "posting_date": "2025-01-01",
            "category_id": cat["category_id"],
            "posting_type": "INCOME",
        },
    )
    client.post(
        "/transfers/",
        json={
            "source_account_id": acc1["account_id"],
            "dest_account_id": acc2["account_id"],
            "debit_amount": "10",
            "credit_amount": "1000",
            "transfer_date": "2025-01-01",
        },
    )

    response = client.delete(f"/accounts/{acc1['account_id']}")

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "posting" in detail
    assert "transfer" in detail


def test_delete_then_recreate_same_name(client):
    """After deleting an account, can create new account with same name."""
    # 1. Arrange: Create and delete an account via API
    create_response = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    delete_response = client.delete(f"/accounts/{account_id}")
    assert delete_response.status_code == 204

    # 2. Act: Create new account with same name
    create_response = client.post(
        "/accounts",
        json={
            "name": "EUR_1",
            "currency": "USD",
            "initial_balance": 0,
        },
    )

    # 3. Assert
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "EUR_1"


def test_update_account_name_success(client):
    """Successfully update an account name."""
    # 1. Arrange: Create account via API
    create_response = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    # 2. Act: Update the account name
    response = client.patch(
        f"/accounts/{account_id}",
        json={"name": "New Account Name"},
    )

    # 3. Assert: Check response and verify update
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Account Name"
    assert data["account_id"] == account_id

    # Verify update in database
    get_response = client.get(f"/accounts/{account_id}")
    assert get_response.json()["name"] == "New Account Name"


def test_update_account_name_duplicate(client):
    """Updating account name to an existing name returns 409."""
    # 1. Arrange: Create two accounts via API
    acc1 = client.post(
        "/accounts",
        json={"name": "EUR_1", "currency": "EUR", "initial_balance": "35"},
    ).json()
    client.post(
        "/accounts",
        json={"name": "RUB_1", "currency": "RUB", "initial_balance": "0"},
    )

    # 2. Act: Try to update first account with second account's name
    response = client.patch(
        f"/accounts/{acc1['account_id']}",
        json={"name": "RUB_1"},
    )

    # 3. Assert: Check response
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_account_name_not_found(client):
    """Updating a non-existent account returns 404."""
    response = client.patch(
        "/accounts/nonexistent-id",
        json={"name": "New Name"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_create_account_with_is_savings(client):
    """POST with is_savings=true returns is_savings in response."""
    response = client.post(
        "/accounts",
        json={
            "name": "Savings Account",
            "currency": "EUR",
            "initial_balance": "100",
            "is_savings": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_savings"] is True


def test_create_account_default_is_savings_false(client):
    """POST without is_savings defaults to false."""
    response = client.post(
        "/accounts",
        json={"name": "Regular Account", "currency": "EUR", "initial_balance": "50"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_savings"] is False


def test_get_account_includes_is_savings(client):
    """GET returns is_savings field."""
    create_response = client.post(
        "/accounts",
        json={
            "name": "Savings Test",
            "currency": "USD",
            "initial_balance": "200",
            "is_savings": True,
        },
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    response = client.get(f"/accounts/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_savings"] is True


def test_get_account_includes_balance(client):
    """GET /accounts/{id} includes balance field equal to initial_balance when no postings."""
    create_response = client.post(
        "/accounts",
        json={"name": "Balance Test", "currency": "EUR", "initial_balance": "100"},
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    response = client.get(f"/accounts/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert "balance" in data
    assert Decimal(data["balance"]) == Decimal("100")


def test_account_balance_reflects_postings(client):
    """Balance is reduced after creating an expense posting."""
    # Create account with initial_balance=100
    acc = client.post(
        "/accounts",
        json={"name": "Expense Test", "currency": "EUR", "initial_balance": "100"},
    ).json()
    account_id = acc["account_id"]

    # Create category hierarchy (required for posting)
    parent = client.post("/categories/", json={"name": "Food", "category_type": "EXPENSE"}).json()
    cat = client.post(
        "/categories/",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    ).json()

    # Create an expense posting of 30
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "30",
            "posting_date": "2025-01-01",
            "category_id": cat["category_id"],
            "posting_type": "EXPENSE",
        },
    )

    # GET account and verify balance = 100 - 30 = 70
    response = client.get(f"/accounts/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["balance"]) == Decimal("70")


def test_create_account_with_description(client):
    """POST with description stores and returns it."""
    response = client.post(
        "/accounts",
        json={
            "name": "My Account",
            "currency": "EUR",
            "initial_balance": "0",
            "description": "My main spending account",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "My main spending account"


def test_create_account_description_defaults_to_none(client):
    """POST without description returns null description."""
    response = client.post(
        "/accounts",
        json={"name": "My Account", "currency": "EUR", "initial_balance": "0"},
    )
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_update_account_description_only(client):
    """PATCH with only description updates it without touching name."""
    create_resp = client.post(
        "/accounts",
        json={"name": "My Account", "currency": "EUR", "initial_balance": "0"},
    )
    account_id = create_resp.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"description": "A fresh description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "A fresh description"
    assert data["name"] == "My Account"  # unchanged


def test_update_account_name_preserves_description(client):
    """PATCH with only name does not clear an existing description."""
    create_resp = client.post(
        "/accounts",
        json={
            "name": "My Account",
            "currency": "EUR",
            "initial_balance": "0",
            "description": "Keep me",
        },
    )
    account_id = create_resp.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"name": "Renamed Account"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Renamed Account"
    assert data["description"] == "Keep me"  # preserved


def test_update_account_name_and_description(client):
    """PATCH with both name and description updates both."""
    create_resp = client.post(
        "/accounts",
        json={"name": "Original", "currency": "EUR", "initial_balance": "0"},
    )
    account_id = create_resp.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"name": "Updated", "description": "New description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "New description"


def test_list_accounts_includes_balance(client):
    """GET /accounts returns balance field for each account."""
    client.post(
        "/accounts",
        json={"name": "Account One", "currency": "EUR", "initial_balance": "50"},
    )
    client.post(
        "/accounts",
        json={"name": "Account Two", "currency": "USD", "initial_balance": "200"},
    )

    response = client.get("/accounts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for account in data:
        assert "balance" in account
    balances = {a["name"]: Decimal(a["balance"]) for a in data}
    assert balances["Account One"] == Decimal("50")
    assert balances["Account Two"] == Decimal("200")


def test_update_account_reject_empty_body(client):
    """AccountUpdate must reject empty PATCH body {} with 422."""
    create_response = client.post(
        "/accounts",
        json={"name": "Test Account", "currency": "EUR", "initial_balance": "100"},
    )
    account_id = create_response.json()["account_id"]

    response = client.patch(f"/accounts/{account_id}", json={})
    assert response.status_code == 422


def test_update_account_reject_null_name(client):
    """AccountUpdate must reject explicit name=null with 422."""
    create_response = client.post(
        "/accounts",
        json={"name": "Test Account", "currency": "EUR", "initial_balance": "100"},
    )
    account_id = create_response.json()["account_id"]

    response = client.patch(f"/accounts/{account_id}", json={"name": None})
    assert response.status_code == 422


def test_create_account_description_too_long_rejected(client):
    """create_account must reject description > 500 chars with 422."""
    long_description = "a" * 501
    response = client.post(
        "/accounts",
        json={
            "name": "Long Desc Account",
            "currency": "EUR",
            "initial_balance": "0",
            "description": long_description,
        },
    )
    assert response.status_code == 422


def test_update_account_description_too_long_rejected(client):
    """update_account must reject description > 500 chars with 422."""
    create_response = client.post(
        "/accounts",
        json={"name": "Test Account", "currency": "EUR", "initial_balance": "100"},
    )
    account_id = create_response.json()["account_id"]

    long_description = "a" * 501
    response = client.patch(
        f"/accounts/{account_id}",
        json={"description": long_description},
    )
    assert response.status_code == 422


def test_update_account_is_atomic(client, monkeypatch):
    """Combined name+description PATCH is atomic (rollback on failure)."""

    def mock_update_account(*args, **kwargs):
        raise Exception("Simulated service failure before commit")

    monkeypatch.setattr("app.api.routers.accounts.update_account", mock_update_account)

    create_response = client.post(
        "/accounts",
        json={"name": "Original Name", "currency": "EUR", "initial_balance": "100"},
    )
    account_id = create_response.json()["account_id"]

    with pytest.raises(Exception, match="Simulated service failure before commit"):
        client.patch(
            f"/accounts/{account_id}",
            json={"name": "New Name", "description": "New Description"},
        )

    # Check if name was NOT persisted
    response = client.get(f"/accounts/{account_id}")
    assert response.json()["name"] == "Original Name"


def test_update_account_initial_balance_success(client):
    """Successfully update an account's initial_balance."""
    create_response = client.post(
        "/accounts",
        json={"name": "Balance Test", "currency": "EUR", "initial_balance": "100"},
    )
    assert create_response.status_code == 201
    account_id = create_response.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"initial_balance": "250.50"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["initial_balance"] == "250.50"
    assert data["balance"] == "250.50"

    # Verify persisted
    get_response = client.get(f"/accounts/{account_id}")
    assert get_response.json()["initial_balance"] == "250.50"


def test_update_account_initial_balance_to_zero(client):
    """Setting initial_balance to 0 is allowed."""
    create_response = client.post(
        "/accounts",
        json={"name": "Zero Test", "currency": "EUR", "initial_balance": "500"},
    )
    account_id = create_response.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"initial_balance": "0"},
    )

    assert response.status_code == 200
    assert Decimal(response.json()["initial_balance"]) == Decimal("0")


def test_update_account_initial_balance_negative_rejected(client):
    """Negative initial_balance is rejected with 422."""
    create_response = client.post(
        "/accounts",
        json={"name": "Neg Test", "currency": "EUR", "initial_balance": "100"},
    )
    account_id = create_response.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"initial_balance": "-50"},
    )

    assert response.status_code == 422


def test_update_account_initial_balance_preserves_other_fields(client):
    """Updating initial_balance does not clear name or description."""
    create_response = client.post(
        "/accounts",
        json={
            "name": "Preserve Test",
            "currency": "EUR",
            "initial_balance": "100",
            "description": "My description",
        },
    )
    account_id = create_response.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"initial_balance": "200"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Preserve Test"
    assert data["description"] == "My description"
    assert Decimal(data["initial_balance"]) == Decimal("200")


def test_update_account_initial_balance_only_field(client):
    """initial_balance alone satisfies the 'at least one field' requirement."""
    create_response = client.post(
        "/accounts",
        json={"name": "Solo Test", "currency": "EUR", "initial_balance": "50"},
    )
    account_id = create_response.json()["account_id"]

    response = client.patch(
        f"/accounts/{account_id}",
        json={"initial_balance": "75"},
    )

    assert response.status_code == 200
    assert Decimal(response.json()["initial_balance"]) == Decimal("75")
