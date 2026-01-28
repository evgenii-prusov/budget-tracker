from decimal import Decimal


def create_test_resources(client):
    # Create account
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Test Posting Account",
            "currency": "EUR",
            "initial_balance": "100.00",
        },
    )
    assert acc_response.status_code == 201
    account_id = acc_response.json()["account_id"]

    # Create category
    cat_response = client.post("/categories/", json={"name": "Test Category"})
    assert cat_response.status_code == 201
    category_id = cat_response.json()["category_id"]

    return account_id, category_id


def test_create_posting_expense_success(client):
    account_id, category_id = create_test_resources(client)

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": "2023-01-15",
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("-50.00")
    assert posting_response["posting_date"] == "2023-01-15"
    assert posting_response["posting_type"] == "EXPENSE"
    assert posting_response["category_id"] == category_id
    assert "posting_id" in posting_response


def test_create_posting_income_success(client):
    account_id, category_id = create_test_resources(client)

    posting_data = {
        "account_id": account_id,
        "amount": "75.50",
        "posting_date": "2023-02-20",
        "posting_type": "INCOME",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("75.50")
    assert posting_response["posting_date"] == "2023-02-20"
    assert posting_response["posting_type"] == "INCOME"
    assert posting_response["category_id"] == category_id
    assert "posting_id" in posting_response


def test_create_posting_no_category_success(client):
    # Only create account
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Test Account No Cat",
            "currency": "EUR",
            "initial_balance": "100.00",
        },
    )
    account_id = acc_response.json()["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "25.00",
        "posting_date": "2023-03-10",
        "posting_type": "EXPENSE",
        # category_id omitted
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 201
    posting_response = response.json()

    assert posting_response["account_id"] == account_id
    assert Decimal(posting_response["amount"]) == Decimal("-25.00")
    assert posting_response["posting_date"] == "2023-03-10"
    assert posting_response["posting_type"] == "EXPENSE"
    assert posting_response["category_id"] is None


def test_create_posting_account_not_found(client):
    # Create only category
    cat_response = client.post("/categories/", json={"name": "Test Category For Fail"})
    category_id = cat_response.json()["category_id"]

    posting_data = {
        "account_id": "non-existent-account-id",
        "amount": "50.00",
        "posting_date": "2023-01-15",
        "posting_type": "EXPENSE",
        "category_id": category_id,
    }

    response = client.post("/postings/", json=posting_data)
    assert response.status_code == 400
    assert (
        "Account with id 'non-existent-account-id' not found"
        in response.json()["detail"]
    )


def test_create_posting_category_not_found(client):
    # Create only account
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Test Account For Fail",
            "currency": "EUR",
            "initial_balance": "100.00",
        },
    )
    account_id = acc_response.json()["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": "2023-01-15",
        "posting_type": "EXPENSE",
        "category_id": "non-existent-category-id",
    }

    response = client.post("/postings/", json=posting_data)
    assert response.status_code == 400
    assert (
        "Category with id 'non-existent-category-id' not found"
        in response.json()["detail"]
    )


def test_create_posting_insufficient_funds(client):
    # Create account with low balance
    acc_response = client.post(
        "/accounts/",
        json={
            "name": "Low Balance Account",
            "currency": "EUR",
            "initial_balance": "10.00",
        },
    )
    account_id = acc_response.json()["account_id"]

    posting_data = {
        "account_id": account_id,
        "amount": "50.00",
        "posting_date": "2023-01-15",
        "posting_type": "EXPENSE",
        "category_id": None,
    }

    response = client.post("/postings/", json=posting_data)

    assert response.status_code == 422
    assert (
        "Insufficient funds in account 'Low Balance Account'"
        in response.json()["detail"]
    )
