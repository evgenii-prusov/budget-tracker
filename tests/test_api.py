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

    # Clean up override
    app.dependency_overrides.clear()


def test_create_account_duplicate_name(session, acc_eur):
    # 1. Arrange: Add an account to the database
    session.add(acc_eur)
    session.commit()

    # 2. Arrange: Override the dependency to use the test session
    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    # 3. Act: Try to create an account with the same name
    response = client.post(
        "/accounts",
        json={
            "name": acc_eur.name,
            "currency": "USD",
            "initial_balance": 100.0,
        },
    )

    # 4. Assert: Check the response
    assert response.status_code == 409
    data = response.json()
    assert "already exists" in data["detail"]
    assert acc_eur.name in data["detail"]

    # Clean up override
    app.dependency_overrides.clear()
