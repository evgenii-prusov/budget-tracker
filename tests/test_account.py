import pytest
from decimal import Decimal
from datetime import date

from budget_tracker.model import Account
from budget_tracker.model import transfer

JAN0125: date = date.fromisoformat("2025-01-01")


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
        Decimal("-2"), JAN0125, category="TAXI", category_type="EXPENSE"
    )
    acc_eur.record_transaction(
        Decimal("-3"), JAN0125, category="TRAVEL", category_type="EXPENSE"
    )

    assert acc_eur.balance == Decimal("30")


def test_transfer_with_different_currencies(
    acc_eur: Account, acc_rub: Account
):
    debit_tx, credit_tx = transfer(
        acc_eur,
        acc_rub,
        JAN0125,
        debit_amt=Decimal(10),
        credit_amt=Decimal(1000),
    )

    assert acc_eur.balance == Decimal(25)
    assert acc_rub.balance == Decimal(1000)
    assert debit_tx.date == credit_tx.date


def test_transaction_keeps_category(acc_eur: Account):
    acc_eur.record_transaction(
        Decimal("3"),
        JAN0125,
        "Taxi",
        category_type="EXPENSE",
    )
    assert acc_eur._transactions.pop().category == "Taxi"
