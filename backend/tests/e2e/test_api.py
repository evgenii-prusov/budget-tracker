import pytest
from decimal import Decimal
from datetime import date

from app.domain.model import Transfer, PostingType


def test_get_account_success(client, session, acc_eur):
    # 1. Arrange: Prepare data in the test database
    session.add(acc_eur)
    session.commit()

    # 2. Act: Make the request
    response = client.get("/accounts/a1")

    # 3. Assert: Check status code and account properties
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == acc_eur.account_id
    assert data["name"] == acc_eur.name
    assert data["currency"] == acc_eur.currency
    assert Decimal(data["initial_balance"]) == acc_eur.initial_balance


def test_get_account_not_found(client, session):
    # 1. Arrange: no data in database
    # 2. Act: Make the request
    response = client.get("/accounts/a1")

    # 3. Assert: Check if 404 error code has been returned
    assert response.status_code == 404


def test_get_accounts(client, session, acc_eur):
    # 1. Arrange: Prepare data in the test database
    session.add(acc_eur)
    session.commit()

    # 2. Act: Make the request
    response = client.get("/accounts")

    # 3. Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["account_id"] == acc_eur.account_id
    assert data[0]["name"] == acc_eur.name


def test_get_accounts_empty_database(client):
    # 1. Arrange: Empty database (no accounts added)

    # 2. Act: Make the request
    response = client.get("/accounts")

    # 3. Assert: Check the response returns empty list
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_create_account_duplicate_name(client, session, acc_eur):
    # 1. Arrange: Add an account to the database
    session.add(acc_eur)
    session.commit()

    # 2. Act: Try to create an account with the same name
    response = client.post(
        "/accounts",
        json={
            "name": acc_eur.name,
            "currency": "USD",
            "initial_balance": 100.0,
        },
    )

    # 3. Assert: Check the response
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]
    assert acc_eur.name in data["detail"]


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


@pytest.mark.parametrize(
    "initial_balance, expected_balance",
    [
        ("100.50", "100.50"),  # Two decimal places
        ("0.01", "0.01"),  # Small decimal
        ("123.456789", "123.456789"),  # High precision
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
    Verify that high precision is preserved through a full save-load cycle.
    """
    # Arrange & Act: Create an account with precise decimal value
    create_response = client.post(
        "/accounts",
        json={
            "name": "Precision Flow Test",
            "currency": "EUR",
            "initial_balance": "999.99999",
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
    assert Decimal(saved_account["initial_balance"]) == Decimal("999.99999")


def test_delete_account_success(client, session, acc_eur):
    """Successfully delete an account with no transfers."""
    # 1. Arrange: Add account to database
    session.add(acc_eur)
    session.commit()

    # 2. Act: Delete the account
    response = client.delete(f"/accounts/{acc_eur.account_id}")

    # 3. Assert: Check response and verify deletion
    assert response.status_code == 204

    # Verify account is gone
    get_response = client.get("/accounts")
    assert get_response.status_code == 200
    assert get_response.json() == []


def test_delete_account_with_postings_succeeds(client, session, acc_eur):
    """Delete succeeds when account has postings (cascade tested in integration)."""
    # 1. Arrange: Add account with a posting
    # Create a posting directly in domain model to simulate history
    acc_eur.record_posting(
        Decimal(100),
        date(2025, 1, 1),
        category_id="legacy",
        posting_type=PostingType.INCOME,
    )
    session.add(acc_eur)
    session.commit()

    # 2. Act: Delete the account
    response = client.delete(f"/accounts/{acc_eur.account_id}")

    # 3. Assert
    assert response.status_code == 204

    # Verify account and postings are gone
    get_response = client.get("/accounts")
    assert get_response.json() == []


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


def test_delete_account_with_transfer_returns_409(client, session, acc_eur, acc_rub):
    """Cannot delete account involved in a transfer."""
    # 1. Arrange: Create two accounts and a transfer between them
    session.add(acc_eur)
    session.add(acc_rub)

    transfer = Transfer(
        transfer_id="t-1",
        source_account_id=acc_eur.account_id,
        dest_account_id=acc_rub.account_id,
        debit_amount=Decimal(10),
        credit_amount=Decimal(1000),  # Different currency
        transfer_date=date(2025, 1, 1),
    )
    session.add(transfer)
    session.commit()

    # 2. Act: Try to delete source account
    response = client.delete(f"/accounts/{acc_eur.account_id}")

    # 3. Assert
    assert response.status_code == 409
    data = response.json()
    assert "Cannot delete" in data["detail"]
    assert "transfer" in data["detail"]

    # Verify account still exists
    get_response = client.get("/accounts")
    assert len(get_response.json()) == 2


def test_delete_account_destination_of_transfer_returns_409(
    client, session, acc_eur, acc_rub
):
    """Cannot delete account that is destination of a transfer."""
    # 1. Arrange
    session.add(acc_eur)
    session.add(acc_rub)

    transfer = Transfer(
        transfer_id="t-1",
        source_account_id=acc_eur.account_id,
        dest_account_id=acc_rub.account_id,
        debit_amount=Decimal(10),
        credit_amount=Decimal(1000),
        transfer_date=date(2025, 1, 1),
    )
    session.add(transfer)
    session.commit()

    # 2. Act: Try to delete destination account
    response = client.delete(f"/accounts/{acc_rub.account_id}")

    # 3. Assert
    assert response.status_code == 409
    assert "Cannot delete" in response.json()["detail"]


def test_delete_then_recreate_same_name(client, session, acc_eur):
    """After deleting an account, can create new account with same name."""
    # 1. Arrange: Create and delete an account
    session.add(acc_eur)
    session.commit()

    delete_response = client.delete(f"/accounts/{acc_eur.account_id}")
    assert delete_response.status_code == 204

    # 2. Act: Create new account with same name
    create_response = client.post(
        "/accounts",
        json={
            "name": acc_eur.name,
            "currency": "USD",
            "initial_balance": 0,
        },
    )

    # 3. Assert
    assert create_response.status_code == 201
    assert create_response.json()["name"] == acc_eur.name


def test_update_account_name_success(client, session, acc_eur):
    """Successfully update an account name."""
    # 1. Arrange: Add account to database
    session.add(acc_eur)
    session.commit()

    # 2. Act: Update the account name
    response = client.patch(
        f"/accounts/{acc_eur.account_id}",
        json={"name": "New Account Name"},
    )

    # 3. Assert: Check response and verify update
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Account Name"
    assert data["account_id"] == acc_eur.account_id

    # Verify update in database
    get_response = client.get(f"/accounts/{acc_eur.account_id}")
    assert get_response.json()["name"] == "New Account Name"


def test_update_account_name_duplicate(client, session, acc_eur, acc_rub):
    """Updating account name to an existing name returns 409."""
    # 1. Arrange: Add two accounts to database
    session.add(acc_eur)
    session.add(acc_rub)
    session.commit()

    # 2. Act: Try to update first account with second account's name
    response = client.patch(
        f"/accounts/{acc_eur.account_id}",
        json={"name": acc_rub.name},
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
