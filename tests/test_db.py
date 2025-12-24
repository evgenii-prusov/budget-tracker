from decimal import Decimal
from datetime import date
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import pytest

from budget_tracker.model import Account, Transaction


def test_account_mapper_loads_accounts(session):
    session.execute(
        text(
            "INSERT INTO account (id, name, currency, initial_balance) VALUES "
            '("acc-1", "Revolut 1", "EUR", "25"),'
            '("acc-2", "Revolut 2",  "EUR", "0"),'
            '("acc-3", "Sparkasse",    "EUR", "100")'
        )
    )
    expected: set[Account] = {
        Account("acc-1", "Revolut 1", "EUR", Decimal("25")),
        Account("acc-2", "Revolut 2", "EUR", Decimal("0")),
        Account("acc-3", "Sparkasse", "EUR", Decimal("100")),
    }
    assert set(session.query(Account).all()) == expected


def test_transaction_mapper_persists_and_loads_transactions(session):
    """Test transactions can be persisted and loaded from database."""
    # Create an account
    account = Account("acc-1", "Test Account", "EUR", Decimal("100"))
    session.add(account)
    session.commit()
    
    # Create and persist a transaction
    tx = Transaction(
        id="tx-1",
        account_id="acc-1",
        amount=Decimal("50"),
        date=date(2024, 1, 15),
        category="Groceries",
        category_type="EXPENSE",
    )
    session.add(tx)
    session.commit()
    
    # Clear the session to ensure we're loading from the database
    session.expunge_all()
    
    # Load the transaction
    loaded_tx = session.query(Transaction).filter_by(id="tx-1").one()
    
    assert loaded_tx.id == "tx-1"
    assert loaded_tx.account_id == "acc-1"
    assert loaded_tx.amount == Decimal("50")
    assert loaded_tx.date == date(2024, 1, 15)
    assert loaded_tx.category == "Groceries"
    assert loaded_tx.category_type == "EXPENSE"


def test_transaction_account_relationship_forward(session):
    """Test that transactions can access their account via the backref."""
    # Create an account
    account = Account("acc-1", "Test Account", "EUR", Decimal("100"))
    session.add(account)
    session.commit()
    
    # Create a transaction
    tx = Transaction(
        id="tx-1",
        account_id="acc-1",
        amount=Decimal("50"),
        date=date(2024, 1, 15),
        category="Groceries",
        category_type="EXPENSE",
    )
    session.add(tx)
    session.commit()
    
    # Clear the session to ensure we're loading from the database
    session.expunge_all()
    
    # Load the transaction and access its account via backref
    loaded_tx = session.query(Transaction).filter_by(id="tx-1").one()
    
    assert loaded_tx.account is not None
    assert loaded_tx.account.id == "acc-1"
    assert loaded_tx.account.name == "Test Account"


def test_transaction_account_relationship_backward(session):
    """Test accounts can access their transactions via relationship."""
    # Create an account
    account = Account("acc-1", "Test Account", "EUR", Decimal("100"))
    session.add(account)
    session.commit()
    
    # Create multiple transactions
    tx1 = Transaction(
        id="tx-1",
        account_id="acc-1",
        amount=Decimal("50"),
        date=date(2024, 1, 15),
        category="Groceries",
        category_type="EXPENSE",
    )
    tx2 = Transaction(
        id="tx-2",
        account_id="acc-1",
        amount=Decimal("30"),
        date=date(2024, 1, 20),
        category="Salary",
        category_type="INCOME",
    )
    session.add(tx1)
    session.add(tx2)
    session.commit()
    
    # Clear the session to ensure we're loading from the database
    session.expunge_all()
    
    # Load the account and access its transactions
    loaded_account = session.query(Account).filter_by(id="acc-1").one()
    
    assert len(loaded_account._transactions) == 2
    tx_ids = {tx.id for tx in loaded_account._transactions}
    assert tx_ids == {"tx-1", "tx-2"}


def test_transaction_foreign_key_constraint_enforced(session):
    """Test foreign key constraint prevents invalid account_id."""
    # Try to create a transaction with a non-existent account_id
    tx = Transaction(
        id="tx-1",
        account_id="non-existent-account",
        amount=Decimal("50"),
        date=date(2024, 1, 15),
        category="Groceries",
        category_type="EXPENSE",
    )
    session.add(tx)
    
    # This should raise an IntegrityError due to foreign key constraint
    with pytest.raises(IntegrityError):
        session.commit()


def test_transactions_associated_with_correct_accounts(session):
    """Test transactions are properly associated with accounts."""
    # Create two accounts
    account1 = Account("acc-1", "Account 1", "EUR", Decimal("100"))
    account2 = Account("acc-2", "Account 2", "USD", Decimal("200"))
    session.add(account1)
    session.add(account2)
    session.commit()
    
    # Create transactions for each account
    tx1 = Transaction(
        id="tx-1",
        account_id="acc-1",
        amount=Decimal("50"),
        date=date(2024, 1, 15),
        category="Groceries",
        category_type="EXPENSE",
    )
    tx2 = Transaction(
        id="tx-2",
        account_id="acc-2",
        amount=Decimal("30"),
        date=date(2024, 1, 20),
        category="Dining",
        category_type="EXPENSE",
    )
    tx3 = Transaction(
        id="tx-3",
        account_id="acc-1",
        amount=Decimal("100"),
        date=date(2024, 1, 25),
        category="Salary",
        category_type="INCOME",
    )
    session.add(tx1)
    session.add(tx2)
    session.add(tx3)
    session.commit()
    
    # Clear the session to ensure we're loading from the database
    session.expunge_all()
    
    # Load accounts and verify each has the correct transactions
    loaded_account1 = session.query(Account).filter_by(id="acc-1").one()
    loaded_account2 = session.query(Account).filter_by(id="acc-2").one()
    
    account1_tx_ids = {tx.id for tx in loaded_account1._transactions}
    account2_tx_ids = {tx.id for tx in loaded_account2._transactions}
    
    assert account1_tx_ids == {"tx-1", "tx-3"}
    assert account2_tx_ids == {"tx-2"}
    
    # Verify that each transaction's backref points to the correct account
    for tx in loaded_account1._transactions:
        assert tx.account.id == "acc-1"
    for tx in loaded_account2._transactions:
        assert tx.account.id == "acc-2"
