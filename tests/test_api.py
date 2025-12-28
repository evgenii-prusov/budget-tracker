from decimal import Decimal
from fastapi.testclient import TestClient
from budget_tracker.api import app

client = TestClient(app)

# Constants for validation
ACCOUNT_NAME_MIN_LENGTH = 3
ACCOUNT_NAME_MAX_LENGTH = 100


def test_get_accounts(session, acc_eur, override_db_session):
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


def test_get_accounts_empty_database(session, override_db_session):
    # 1. Arrange: Empty database (no accounts added)

    # 2. Act: Make the request
    response = client.get("/accounts")

    # 3. Assert: Check the response returns empty list
    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_create_account_duplicate_name(session, acc_eur, override_db_session):
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


def test_create_account_with_valid_currency(session, override_db_session):
    # Act: Create an account with a valid currency
    response = client.post(
        "/accounts",
        json={
            "name": "Test Account",
            "currency": "USD",
            "initial_balance": 100.0,
        },
    )

    # Assert: Check the response
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_create_account_with_invalid_currency(session, override_db_session):
    # Act: Try to create an account with an invalid currency
    response = client.post(
        "/accounts",
        json={
            "name": "Test Account",
            "currency": "INVALID",
            "initial_balance": 100.0,
        },
    )

    # Assert: Check that validation fails
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_create_account_normalizes_currency_case(session, override_db_session):
    # Act: Create an account with lowercase currency code
    response = client.post(
        "/accounts",
        json={
            "name": "Test Account",
            "currency": "eur",
            "initial_balance": 50.0,
        },
    )

    # Assert: Currency should be normalized to uppercase
    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_create_account_with_decimal_precision_two_places(
    session, override_db_session
):
    # Act: Create an account with two decimal places
    response = client.post(
        "/accounts",
        json={
            "name": "Decimal Test 2",
            "currency": "USD",
            "initial_balance": "100.50",
        },
    )

    # Assert: Decimal precision should be preserved
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["initial_balance"]) == Decimal("100.50")


def test_create_account_with_small_decimal_value(
    session, override_db_session
):
    # Act: Create an account with a very small decimal value
    response = client.post(
        "/accounts",
        json={
            "name": "Small Decimal Test",
            "currency": "USD",
            "initial_balance": "0.01",
        },
    )

    # Assert: Small decimal value should be preserved
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["initial_balance"]) == Decimal("0.01")


def test_create_account_with_many_decimal_places(
    session, override_db_session
):
    # Act: Create an account with many decimal places
    response = client.post(
        "/accounts",
        json={
            "name": "Many Decimals Test",
            "currency": "USD",
            "initial_balance": "123.456789",
        },
    )

    # Assert: Decimal precision should be preserved
    assert response.status_code == 201
    data = response.json()
    assert Decimal(data["initial_balance"]) == Decimal("123.456789")


def test_decimal_precision_through_create_and_get_flow(
    session, override_db_session
):
    # Arrange & Act: Create an account with precise decimal value
    create_response = client.post(
        "/accounts",
        json={
            "name": "Precision Flow Test",
            "currency": "EUR",
            "initial_balance": "999.99",
        },
    )

    # Assert: Account created successfully
    assert create_response.status_code == 201
    created_data = create_response.json()
    assert Decimal(created_data["initial_balance"]) == Decimal("999.99")
    account_id = created_data["id"]

    # Act: Retrieve all accounts to verify decimal is preserved
    get_response = client.get("/accounts")

    # Assert: Decimal precision preserved through full flow
    assert get_response.status_code == 200
    accounts = get_response.json()
    account = next((a for a in accounts if a["id"] == account_id), None)
    assert account is not None
    assert Decimal(account["initial_balance"]) == Decimal("999.99")
