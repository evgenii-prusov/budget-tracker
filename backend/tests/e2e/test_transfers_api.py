def test_create_transfer_source_account_not_found(client, session, acc_rub):
    # 1. Arrange: Create only destination account
    session.add(acc_rub)
    session.commit()

    # 2. Act: Try to transfer from non-existent account
    transfer_data = {
        "source_account_id": "non-existent",
        "dest_account_id": acc_rub.account_id,
        "debit_amount": "100.00",
        "credit_amount": "8000.00",
        "transfer_date": "2026-01-28",
    }
    response = client.post("/transfers/", json=transfer_data)

    # 3. Assert
    assert response.status_code == 400
    assert "Source account" in response.json()["detail"]


def test_create_transfer_dest_account_not_found(client, session, acc_eur):
    # 1. Arrange: Create only source account
    session.add(acc_eur)
    session.commit()

    # 2. Act: Try to transfer to non-existent account
    transfer_data = {
        "source_account_id": acc_eur.account_id,
        "dest_account_id": "non-existent",
        "debit_amount": "100.00",
        "credit_amount": "8000.00",
        "transfer_date": "2026-01-28",
    }
    response = client.post("/transfers/", json=transfer_data)

    # 3. Assert
    assert response.status_code == 400
    assert "Destination account" in response.json()["detail"]
