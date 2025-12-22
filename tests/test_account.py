import pytest
from decimal import Decimal
from datetime import date

from budget_tracker.model import Account
from budget_tracker.model import transfer


@pytest.fixture
def eur_account() -> Account:
    return Account("a1", "EUR_1", "EUR", Decimal("35"))


@pytest.fixture
def rub_account() -> Account:
    return Account("a2", "RUB_1", "RUB", Decimal("0"))


def test_account_balance_is_sum_of_init_balance_and_transactions(eur_account):
    eur_account.record_transaction(
        Decimal("-2"), date.fromisoformat("2025-01-01")
    )
    eur_account.record_transaction(
        Decimal("-3"), date.fromisoformat("2025-01-01")
    )

    assert eur_account.balance == Decimal("30")


def test_transfer_with_different_currencies(eur_account, rub_account):
    debit_tx, credit_tx = transfer(
        eur_account,
        rub_account,
        date.fromisoformat("2025-01-01"),
        debit_amt=Decimal(10),
        credit_amt=Decimal(1000),
    )

    assert eur_account.balance == Decimal(25)
    assert rub_account.balance == Decimal(1000)
    assert debit_tx.date == credit_tx.date


def test_transaction_keeps_category(eur_account: Account):
    eur_account.record_transaction(
        Decimal("3"), date.fromisoformat("2025-01-01"), "Taxi"
    )
    assert eur_account._transactions.pop().category == "Taxi"
