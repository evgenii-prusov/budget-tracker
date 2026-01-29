def test_create_transfer_source_account_not_found(client):
    # 1. Arrange: Create only destination account via API
    acc = client.post(
        "/accounts",
        json={"name": "RUB_1", "currency": "RUB", "initial_balance": "0"},
    ).json()

    # 2. Act: Try to transfer from non-existent account
    transfer_data = {
        "source_account_id": "non-existent",
        "dest_account_id": acc["account_id"],
        "debit_amount": "100.00",
        "credit_amount": "8000.00",
        "transfer_date": "2026-01-28",
    }
    response = client.post("/transfers/", json=transfer_data)

    # 3. Assert
    assert response.status_code == 400
    assert "Source account" in response.json()["detail"]


def test_create_transfer_dest_account_not_found(client):
    # 1. Arrange: Create only source account via API
    acc = client.post(
        "/accounts",
        json={
            "name": "EUR_1",
            "currency": "EUR",
            "initial_balance": "35",
        },
    ).json()

    # 2. Act: Try to transfer to non-existent account
    transfer_data = {
        "source_account_id": acc["account_id"],
        "dest_account_id": "non-existent",
        "debit_amount": "100.00",
        "credit_amount": "8000.00",
        "transfer_date": "2026-01-28",
    }
    response = client.post("/transfers/", json=transfer_data)

    # 3. Assert
    assert response.status_code == 400
    assert "Destination account" in response.json()["detail"]
