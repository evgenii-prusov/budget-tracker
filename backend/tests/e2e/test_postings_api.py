from decimal import Decimal
from tests.constants import JAN_01, JAN_02, JAN_03


def test_create_posting_expense_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("-50.00")
    assert posting_response["posting_date"] == JAN_01.isoformat()
    assert posting_response["posting_type"] == "EXPENSE"
    assert posting_response["category_id"] == category_id
    assert "posting_id" in posting_response


def test_create_posting_income_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "75.50",
        "posting_date": JAN_02.isoformat(),
        "posting_type": "INCOME",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("75.50")
    assert posting_response["posting_date"] == JAN_02.isoformat()
    assert posting_response["posting_type"] == "INCOME"
    assert posting_response["category_id"] == category_id
    assert "posting_id" in posting_response


def test_create_posting_no_category_success(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "25.00",
        "posting_date": JAN_03.isoformat(),
        "posting_type": "EXPENSE",
        # category_id omitted
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("-25.00")
    assert posting_response["posting_date"] == JAN_03.isoformat()
    assert posting_response["posting_type"] == "EXPENSE"
    assert posting_response["category_id"] is None


def test_create_posting_account_not_found(client, test_data):
    category_id = test_data["category_id"]

    posting_data = {
        "account_id": "non-existent-account-id",
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)
    assert response.status_code == 400
    assert "Account with id 'non-existent-account-id' not found" in response.json()["detail"]


def test_create_posting_category_not_found(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": "non-existent-category-id",
    }

    response = client.post("/postings/", json=posting_data)
    assert response.status_code == 400
    assert "Category with id 'non-existent-category-id' not found" in response.json()["detail"]


def test_create_posting_insufficient_funds(client, test_data):
    account_id = test_data["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "150.00",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "EXPENSE",
        "category_id": None,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 422
    assert "Insufficient funds in account 'Test Posting Account'" in response.json()["detail"]


def test_get_posting_success(client, test_data):
    account_id = test_data["account_id"]
    category_id = test_data["category_id"]

    # Create posting
    posting_data = {
        "account_id": account_id,
        "amount": "123.45",
        "posting_date": JAN_01.isoformat(),
        "posting_type": "INCOME",
        "category_id": category_id,
    }
    create_response = client.post("/postings/", json=posting_data)
    assert create_response.status_code == 201
    posting_id = create_response.json()["posting_id"]

    # Get posting
    response = client.get(f"/postings/{posting_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["posting_id"] == posting_id
    assert data["account_id"] == account_id
    assert Decimal(data["amount"]) == Decimal("123.45")
    assert data["posting_date"] == JAN_01.isoformat()
    assert data["posting_type"] == "INCOME"
    assert data["category_id"] == category_id


def test_get_posting_not_found(client):
    response = client.get("/postings/non-existent-id")
    assert response.status_code == 404
    assert "Posting with id 'non-existent-id' not found" in response.json()["detail"]


def test_list_postings_endpoint(client, test_data):
    account_id = test_data["account_id"]

    # Create two postings
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "20.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    # Act
    response = client.get("/postings/")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_postings_pagination(client, test_data):
    account_id = test_data["account_id"]

    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "20.00",
            "posting_date": JAN_02.isoformat(),
            "posting_type": "EXPENSE",
        },
    )
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "30.00",
            "posting_date": JAN_03.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    response = client.get("/postings/?skip=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["posting_date"] == JAN_02.isoformat()


def test_list_postings_endpoint_filtered(client, test_data):
    account_id = test_data["account_id"]

    # Create another account
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Another Account",
            "currency": "EUR",
            "initial_balance": "100.00",
        },
    )
    another_account_id = acc_response.json()["account_id"]

    # Create posting in original account
    client.post(
        "/postings/",
        json={
            "account_id": account_id,
            "amount": "10.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    # Create posting in another account
    client.post(
        "/postings/",
        json={
            "account_id": another_account_id,
            "amount": "20.00",
            "posting_date": JAN_01.isoformat(),
            "posting_type": "EXPENSE",
        },
    )

    # Act: Get filtered by account_id
    response = client.get(f"/postings/?account_id={account_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    for posting in data:
        assert posting["account_id"] == account_id
