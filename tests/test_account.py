import pytest
from decimal import Decimal
from datetime import date

from budget_tracker.model import Account
from budget_tracker.model import Transaction
from budget_tracker.model import transfer
from budget_tracker.model import InsufficientFundsError

JAN_01_2025 = date.fromisoformat("2025-01-01")
JAN_02_2025 = date.fromisoformat("2025-01-02")
JAN_03_2025 = date.fromisoformat("2025-01-03")


@pytest.fixture
def acc_eur() -> Account:
    return Account("a1", "EUR_1", "EUR", Decimal("35"))


@pytest.fixture
def acc_rub() -> Account:
    return Account("a2", "RUB_1", "RUB", Decimal("0"))


def test_account_balance_is_sum_of_init_balance_and_transactions(
    acc_eur: Account,
):
    acc_eur.record_transaction(
        Decimal("2"), JAN_01_2025, category="TAXI", category_type="EXPENSE"
    )
    acc_eur.record_transaction(
        Decimal("3"), JAN_01_2025, category="TRAVEL", category_type="EXPENSE"
    )
    acc_eur.record_transaction(
        Decimal("500"),
        JAN_01_2025,
        category="KINDERGELD",
        category_type="INCOME",
    )

    assert acc_eur.balance == Decimal("530")


def test_transfer_with_different_currencies(
    acc_eur: Account, acc_rub: Account
):
    debit_tx, credit_tx = transfer(
        acc_eur,
        acc_rub,
        JAN_01_2025,
        debit_amt=Decimal(10),
        credit_amt=Decimal(1000),
    )

    assert acc_eur.balance == Decimal(25)
    assert acc_rub.balance == Decimal(1000)
    assert debit_tx.date == credit_tx.date


def test_transaction_keeps_category(acc_eur: Account):
    acc_eur.record_transaction(
        Decimal("3"),
        JAN_01_2025,
        "Taxi",
        category_type="EXPENSE",
    )
    assert acc_eur._transactions.pop().category == "Taxi"


def test_transactions_sorted_by_date():
    tx_2 = Transaction(
        "tx-2", "a-1", Decimal("3"), JAN_02_2025, "food", "expense"
    )
    tx_1 = Transaction(
        "tx-1", "a-1", Decimal("0"), JAN_01_2025, "taxi", "expense"
    )
    tx_3 = Transaction(
        "tx-3", "a-2", Decimal("1"), JAN_03_2025, "taxi", "expense"
    )

    transactions = [tx_2, tx_1, tx_3]
    transactions.sort()
    assert transactions[0].date == JAN_01_2025
    assert transactions[1].date == JAN_02_2025
    assert transactions[2].date == JAN_03_2025


def test_raise_insufficient_funds_error(acc_eur: Account):
    with pytest.raises(InsufficientFundsError):
        acc_eur.record_transaction(
            Decimal("50"), JAN_01_2025, "some_category", "EXPENSE"
        )
