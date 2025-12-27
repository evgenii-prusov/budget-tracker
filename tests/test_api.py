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


def test_create_account_with_valid_name(override_db_session):
    # Valid account names
    valid_names = [
        "MyAccount",
        "Account 1",
        "My-Account",
        "My_Account",
        "Account-Name_123",
        "ABC",
        "a1b",
    ]

    for name in valid_names:
        response = client.post(
            "/accounts",
            json={"name": name, "currency": "USD", "initial_balance": 100.0},
        )
        assert response.status_code == 201, f"Failed for name: {name}"
        data = response.json()
        assert data["name"] == name


def test_create_account_with_name_too_short(override_db_session):
    # Names shorter than minimum length should fail validation
    short_names = [
        "",  # Empty
        "A",  # 1 character
        "AB",  # 2 characters
    ]

    for name in short_names:
        response = client.post(
            "/accounts",
            json={"name": name, "currency": "USD", "initial_balance": 100.0},
        )
        assert response.status_code == 422, (
            f"Should have failed for name: '{name}'"
        )
        error_detail = response.json()["detail"]
        assert any("name" in str(error).lower() for error in error_detail)


def test_create_account_with_name_too_long(override_db_session):
    # Name longer than max length should fail
    long_name = "A" * (ACCOUNT_NAME_MAX_LENGTH + 1)
    response = client.post(
        "/accounts",
        json={"name": long_name, "currency": "USD", "initial_balance": 100.0},
    )
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("name" in str(error).lower() for error in error_detail)


def test_create_account_with_invalid_name_pattern(override_db_session):
    # Names that don't match the pattern should fail
    invalid_names = [
        " LeadingSpace",  # Starts with space
        "-StartsWithDash",  # Starts with dash
        "_StartsWithUnderscore",  # Starts with underscore
        "Name@Special",  # Contains special character
        "Name!",  # Contains special character
    ]

    for name in invalid_names:
        response = client.post(
            "/accounts",
            json={"name": name, "currency": "USD", "initial_balance": 100.0},
        )
        assert response.status_code == 422, (
            f"Should have failed for name: {name}"
        )
        error_detail = response.json()["detail"]
        assert any("name" in str(error).lower() for error in error_detail)
