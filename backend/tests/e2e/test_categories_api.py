from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text


def test_list_categories_endpoint(client: TestClient, session: Session):
    # Arrange
    session.execute(
        text(
            "INSERT INTO category (category_id, name) VALUES "
            "('c1', 'Food'),"
            "('c2', 'Salary')"
        )
    )
    session.commit()

    # Act
    response = client.get("/categories")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {c["name"] for c in data}
    assert "Food" in names
    assert "Salary" in names


def test_create_category_endpoint(client: TestClient):
    # Act
    response = client.post("/categories", json={"name": "Travel"})

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Travel"
    assert "category_id" in data


def test_create_category_duplicate_returns_409(client: TestClient):
    # Arrange
    client.post("/categories", json={"name": "Travel"})

    # Act
    response = client.post("/categories", json={"name": "Travel"})

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_get_category_endpoint(client: TestClient, session: Session):
    # Arrange
    session.execute(
        text("INSERT INTO category (category_id, name) VALUES ('c1', 'Food')")
    )
    session.commit()

    # Act
    response = client.get("/categories/c1")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"


def test_update_category_endpoint(client: TestClient, session: Session):
    # Arrange
    session.execute(
        text("INSERT INTO category (category_id, name) VALUES ('c1', 'Food')")
    )
    session.commit()

    # Act
    response = client.patch("/categories/c1", json={"name": "Groceries"})

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Groceries"

    # Verify change
    response = client.get("/categories/c1")
    assert response.json()["name"] == "Groceries"


def test_update_category_duplicate_returns_409(client: TestClient, session: Session):
    # Arrange
    session.execute(
        text(
            "INSERT INTO category (category_id, name) VALUES "
            "('c1', 'Food'), ('c2', 'Groceries')"
        )
    )
    session.commit()

    # Act
    response = client.patch("/categories/c1", json={"name": "Groceries"})

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_category_not_found_returns_404(client: TestClient):
    response = client.patch("/categories/non-existent", json={"name": "New Name"})
    assert response.status_code == 404


def test_delete_category_endpoint(client: TestClient, session: Session):
    # Arrange
    session.execute(
        text("INSERT INTO category (category_id, name) VALUES ('c1', 'Food')")
    )
    session.commit()

    # Act
    response = client.delete("/categories/c1")

    # Assert
    assert response.status_code == 204

    # Verify deleted
    response = client.get("/categories/c1")
    assert response.status_code == 404


def test_delete_category_not_found_returns_404(client: TestClient):
    response = client.delete("/categories/non-existent")
    assert response.status_code == 404


def test_delete_category_in_use_returns_409(client: TestClient, session: Session):
    # Arrange: Create category and posting that uses it
    session.execute(
        text("INSERT INTO category (category_id, name) VALUES ('c1', 'Food')")
    )
    session.execute(
        text(
            "INSERT INTO account (account_id, name, currency, initial_balance) "
            "VALUES ('a1', 'Cash', 'USD', 100)"
        )
    )
    session.execute(
        text(
            "INSERT INTO posting "
            "(posting_id, account_id, amount, posting_date, category_id, posting_type) "
            "VALUES ('p1', 'a1', -10, '2024-01-01', 'c1', 'EXPENSE')"
        )
    )
    session.commit()

    # Act
    response = client.delete("/categories/c1")

    # Assert
    assert response.status_code == 409
    assert "has postings" in response.json()["detail"]
