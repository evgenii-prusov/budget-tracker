import pytest
from decimal import Decimal

from budget_tracker.model import Account
from budget_tracker.model import transfer


@pytest.fixture
def eur_account():
    yield Account("acc_1", "Account 1 (EUR)", "EUR", Decimal(35))


@pytest.fixture
def rub_account():
    yield Account("acc_2", "Account 2 (RUB)", "RUB", Decimal(0))


def test_account_balance_is_sum_of_init_balance_and_transactions(eur_account):
    eur_account.record_transaction(Decimal("-2"))
    eur_account.record_transaction(Decimal("-3"))

    assert eur_account.balance == Decimal("30")


def test_transfer_with_different_currencies(eur_account, rub_account):
    transfer(
        eur_account,
        rub_account,
        debit_amt=Decimal(10),
        credit_amt=Decimal(1000),
    )

    assert eur_account.balance == Decimal(25)
    assert rub_account.balance == Decimal(1000)
