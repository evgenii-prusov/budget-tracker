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
