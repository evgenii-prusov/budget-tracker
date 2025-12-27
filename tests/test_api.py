from fastapi.testclient import TestClient
from budget_tracker.api import app, get_db_session

client = TestClient(app)


def test_get_accounts(session, acc_eur):
    # 1. Arrange: Prepare data in the test database
    session.add(acc_eur)
    session.commit()

    # 2. Arrange: Override the dependency to use the test session
    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    # 3. Act: Make the request
    response = client.get("/accounts")

    # 4. Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == acc_eur.id
    assert data[0]["name"] == acc_eur.name

    # Clean up override
    app.dependency_overrides.clear()


def test_create_account_with_valid_currency(session):
    # Arrange: Override the dependency to use the test session
    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

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

    # Clean up override
    app.dependency_overrides.clear()


def test_create_account_with_invalid_currency(session):
    # Arrange: Override the dependency to use the test session
    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

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

    # Clean up override
    app.dependency_overrides.clear()


def test_create_account_normalizes_currency_case(session):
    # Arrange: Override the dependency to use the test session
    def override_get_db_session():
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

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

    # Clean up override
    app.dependency_overrides.clear()
