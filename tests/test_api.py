import pytest
from decimal import Decimal


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
    assert data[0]["id"] == acc_eur.id
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
def test_create_account_precision_and_types(
    client, initial_balance, expected_balance
):
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
    created_id = create_response.json()["id"]

    # Act: Retrieve all accounts
    get_response = client.get("/accounts")

    # Assert
    assert get_response.status_code == 200
    accounts = get_response.json()
    saved_account = next((a for a in accounts if a["id"] == created_id), None)
    assert saved_account is not None, f"Account {created_id} not found"
    assert Decimal(saved_account["initial_balance"]) == Decimal("999.99999")
