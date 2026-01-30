from fastapi.testclient import TestClient


def test_list_categories_endpoint(client: TestClient):
    # Arrange
    client.post("/categories", json={"name": "Food"})
    client.post("/categories", json={"name": "Salary"})

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


def test_get_category_endpoint(client: TestClient):
    # Arrange
    cat = client.post("/categories", json={"name": "Food"}).json()

    # Act
    response = client.get(f"/categories/{cat['category_id']}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"


def test_update_category_endpoint(client: TestClient):
    # Arrange
    cat = client.post("/categories", json={"name": "Food"}).json()
    category_id = cat["category_id"]

    # Act
    response = client.patch(f"/categories/{category_id}", json={"name": "Groceries"})

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Groceries"

    # Verify change
    response = client.get(f"/categories/{category_id}")
    assert response.json()["name"] == "Groceries"


def test_update_category_same_name_succeeds(client: TestClient):
    # Arrange
    cat = client.post("/categories", json={"name": "Food"}).json()
    category_id = cat["category_id"]

    # Act - update to same name
    response = client.patch(f"/categories/{category_id}", json={"name": "Food"})

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Food"


def test_update_category_duplicate_returns_409(client: TestClient):
    # Arrange
    client.post("/categories", json={"name": "Food"})
    cat2 = client.post("/categories", json={"name": "Groceries"}).json()

    # Act
    response = client.patch(
        f"/categories/{cat2['category_id']}",
        json={"name": "Food"},
    )

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_update_category_not_found_returns_404(client: TestClient):
    response = client.patch("/categories/non-existent", json={"name": "New Name"})
    assert response.status_code == 404


def test_delete_category_endpoint(client: TestClient):
    # Arrange
    cat = client.post("/categories", json={"name": "Food"}).json()
    category_id = cat["category_id"]

    # Act
    response = client.delete(f"/categories/{category_id}")

    # Assert
    assert response.status_code == 204

    # Verify deleted
    response = client.get(f"/categories/{category_id}")
    assert response.status_code == 404


def test_delete_category_not_found_returns_404(client: TestClient):
    response = client.delete("/categories/non-existent")
    assert response.status_code == 404


def test_delete_category_in_use_returns_409(client: TestClient):
    # Arrange: Create category, account, and posting via API
    cat = client.post("/categories", json={"name": "Food"}).json()
    acc = client.post(
        "/accounts",
        json={"name": "Cash", "currency": "USD", "initial_balance": 100},
    ).json()
    client.post(
        "/postings/",
        json={
            "account_id": acc["account_id"],
            "amount": 10,
            "posting_date": "2024-01-01",
            "category_id": cat["category_id"],
            "posting_type": "EXPENSE",
        },
    )

    # Act
    response = client.delete(f"/categories/{cat['category_id']}")

    # Assert
    assert response.status_code == 409
    assert "has postings" in response.json()["detail"]


def test_list_categories_pagination(client: TestClient):
    client.post("/categories", json={"name": "Alpha"})
    client.post("/categories", json={"name": "Beta"})
    client.post("/categories", json={"name": "Gamma"})

    response = client.get("/categories?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Beta"
