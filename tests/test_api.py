from fastapi.testclient import TestClient
from budget_tracker.api import app, get_db_session

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
