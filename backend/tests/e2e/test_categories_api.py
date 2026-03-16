from fastapi.testclient import TestClient


def test_unauthorized_returns_401(client_no_auth):
    response = client_no_auth.get("/categories")
    assert response.status_code == 401


def test_list_categories_endpoint(client: TestClient):
    # Arrange
    client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"})
    client.post("/categories", json={"name": "Salary", "category_type": "INCOME"})

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
    response = client.post("/categories", json={"name": "Travel", "category_type": "EXPENSE"})

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Travel"
    assert data["category_type"] == "EXPENSE"
    assert data["parent_id"] is None
    assert "category_id" in data


def test_create_category_duplicate_returns_409(client: TestClient):
    # Arrange
    client.post("/categories", json={"name": "Travel", "category_type": "EXPENSE"})

    # Act
    response = client.post("/categories", json={"name": "Travel", "category_type": "EXPENSE"})

    # Assert
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_get_category_endpoint(client: TestClient):
    # Arrange
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()

    # Act
    response = client.get(f"/categories/{cat['category_id']}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Food"
    assert data["category_type"] == "EXPENSE"


def test_update_category_endpoint(client: TestClient):
    # Arrange
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
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
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    category_id = cat["category_id"]

    # Act - update to same name
    response = client.patch(f"/categories/{category_id}", json={"name": "Food"})

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Food"


def test_update_category_duplicate_returns_409(client: TestClient):
    # Arrange
    client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"})
    cat2 = client.post("/categories", json={"name": "Groceries", "category_type": "EXPENSE"}).json()

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
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
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
    # Arrange: Create parent + subcategory, account, and posting via API
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    cat = client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    ).json()
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
    client.post("/categories", json={"name": "Alpha", "category_type": "EXPENSE"})
    client.post("/categories", json={"name": "Beta", "category_type": "EXPENSE"})
    client.post("/categories", json={"name": "Gamma", "category_type": "EXPENSE"})

    response = client.get("/categories?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Beta"


# --- Category Hierarchy E2E Tests ---


def test_create_subcategory(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    response = client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == parent["category_id"]
    assert data["category_type"] == "EXPENSE"


def test_create_subcategory_of_subcategory_fails(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    child = client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    ).json()
    response = client.post(
        "/categories",
        json={"name": "Organic", "category_type": "EXPENSE", "parent_id": child["category_id"]},
    )
    assert response.status_code == 422
    assert "max 2 levels" in response.json()["detail"]


def test_create_subcategory_type_mismatch_fails(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    response = client.post(
        "/categories",
        json={"name": "Salary", "category_type": "INCOME", "parent_id": parent["category_id"]},
    )
    assert response.status_code == 422
    assert "must match" in response.json()["detail"]


def test_list_parent_categories_with_children(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    )
    client.post(
        "/categories",
        json={
            "name": "Restaurants",
            "category_type": "EXPENSE",
            "parent_id": parent["category_id"],
        },
    )

    response = client.get("/categories/parents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Food"
    assert len(data[0]["children"]) == 2


def test_list_subcategories(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    )
    client.post(
        "/categories",
        json={
            "name": "Restaurants",
            "category_type": "EXPENSE",
            "parent_id": parent["category_id"],
        },
    )

    response = client.get(f"/categories/{parent['category_id']}/children")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {c["name"] for c in data}
    assert "Groceries" in names
    assert "Restaurants" in names


def test_delete_parent_with_children_fails(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    )

    response = client.delete(f"/categories/{parent['category_id']}")
    assert response.status_code == 409
    assert "has child categories" in response.json()["detail"]


# --- Category Description E2E Tests ---


def test_create_category_with_description(client: TestClient):
    response = client.post(
        "/categories",
        json={"name": "Food", "category_type": "EXPENSE", "description": "All food expenses"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "All food expenses"


def test_create_category_without_description_returns_null(client: TestClient):
    response = client.post("/categories", json={"name": "Travel", "category_type": "EXPENSE"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_get_category_returns_description(client: TestClient):
    cat = client.post(
        "/categories",
        json={"name": "Food", "category_type": "EXPENSE", "description": "All food expenses"},
    ).json()
    response = client.get(f"/categories/{cat['category_id']}")
    assert response.status_code == 200
    assert response.json()["description"] == "All food expenses"


def test_update_category_description(client: TestClient):
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    response = client.patch(f"/categories/{cat['category_id']}", json={"description": "Updated"})
    assert response.status_code == 200
    assert response.json()["description"] == "Updated"


def test_update_category_name_and_description(client: TestClient):
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    response = client.patch(
        f"/categories/{cat['category_id']}",
        json={"name": "Groceries", "description": "Weekly groceries"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["description"] == "Weekly groceries"


def test_list_parent_categories_includes_description(client: TestClient):
    client.post(
        "/categories",
        json={"name": "Food", "category_type": "EXPENSE", "description": "Food expenses"},
    )
    response = client.get("/categories/parents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Food expenses"


def test_create_category_description_too_long_returns_422(client: TestClient):
    response = client.post(
        "/categories",
        json={"name": "Food", "category_type": "EXPENSE", "description": "x" * 501},
    )
    assert response.status_code == 422


def test_create_posting_with_parent_that_has_children_fails(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    client.post(
        "/categories",
        json={"name": "Groceries", "category_type": "EXPENSE", "parent_id": parent["category_id"]},
    )
    acc = client.post(
        "/accounts",
        json={"name": "Cash", "currency": "USD", "initial_balance": 100},
    ).json()

    response = client.post(
        "/postings/",
        json={
            "account_id": acc["account_id"],
            "amount": 10,
            "posting_date": "2024-01-01",
            "category_id": parent["category_id"],
            "posting_type": "EXPENSE",
        },
    )
    assert response.status_code == 422
    assert "Use a subcategory" in response.json()["detail"]


# --- Update Category Parent E2E Tests ---


def test_update_category_parent(client: TestClient):
    """Move subcategory from one parent to another."""
    parent1 = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    parent2 = client.post(
        "/categories", json={"name": "Shopping", "category_type": "EXPENSE"}
    ).json()
    child = client.post(
        "/categories",
        json={
            "name": "Groceries",
            "category_type": "EXPENSE",
            "parent_id": parent1["category_id"],
        },
    ).json()

    response = client.patch(
        f"/categories/{child['category_id']}",
        json={"parent_id": parent2["category_id"]},
    )
    assert response.status_code == 200
    assert response.json()["parent_id"] == parent2["category_id"]


def test_update_category_promote_to_root(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    child = client.post(
        "/categories",
        json={
            "name": "Groceries",
            "category_type": "EXPENSE",
            "parent_id": parent["category_id"],
        },
    ).json()

    response = client.patch(
        f"/categories/{child['category_id']}",
        json={"parent_id": None},
    )
    assert response.status_code == 200
    assert response.json()["parent_id"] is None


def test_update_category_parent_type_mismatch_returns_422(client: TestClient):
    income_parent = client.post(
        "/categories", json={"name": "Salary", "category_type": "INCOME"}
    ).json()
    expense_cat = client.post(
        "/categories", json={"name": "Food", "category_type": "EXPENSE"}
    ).json()

    response = client.patch(
        f"/categories/{expense_cat['category_id']}",
        json={"parent_id": income_parent["category_id"]},
    )
    assert response.status_code == 422
    assert "must match" in response.json()["detail"]


def test_update_category_parent_not_found_returns_404(client: TestClient):
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()

    response = client.patch(
        f"/categories/{cat['category_id']}",
        json={"parent_id": "non-existent"},
    )
    assert response.status_code == 404


def test_update_category_with_children_cannot_nest_returns_422(client: TestClient):
    parent = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()
    client.post(
        "/categories",
        json={
            "name": "Groceries",
            "category_type": "EXPENSE",
            "parent_id": parent["category_id"],
        },
    )
    new_parent = client.post(
        "/categories", json={"name": "Shopping", "category_type": "EXPENSE"}
    ).json()

    response = client.patch(
        f"/categories/{parent['category_id']}",
        json={"parent_id": new_parent["category_id"]},
    )
    assert response.status_code == 422
    assert "has children" in response.json()["detail"]


def test_update_category_self_parent_returns_422(client: TestClient):
    cat = client.post("/categories", json={"name": "Food", "category_type": "EXPENSE"}).json()

    response = client.patch(
        f"/categories/{cat['category_id']}",
        json={"parent_id": cat["category_id"]},
    )
    assert response.status_code == 422
    assert "cannot be its own parent" in response.json()["detail"]


def test_create_posting_with_leaf_parent_category_succeeds(client: TestClient):
    """A root category with no children is a leaf — posting is allowed."""
    category = client.post(
        "/categories", json={"name": "Kindergeld", "category_type": "INCOME"}
    ).json()
    acc = client.post(
        "/accounts",
        json={"name": "Checking", "currency": "EUR", "initial_balance": 1000},
    ).json()

    response = client.post(
        "/postings/",
        json={
            "account_id": acc["account_id"],
            "amount": 250,
            "posting_date": "2024-01-15",
            "category_id": category["category_id"],
            "posting_type": "INCOME",
        },
    )
    assert response.status_code == 201
    assert response.json()["category_id"] == category["category_id"]
