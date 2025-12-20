from decimal import Decimal

from budget_tracker.model import Account
from budget_tracker.model import transfer


def test_account_balance_is_sum_of_initial_balance_and_transactions():
    acc_1 = Account(id="acc1", name="Account 1", currency="EUR", initial_balance=Decimal(35))
    acc_1.record_transaction(Decimal("-2"))
    acc_1.record_transaction(Decimal("-3"))

    assert acc_1.balance == Decimal("30")

def test_transfer_with_different_currencies():
    acc_1 = Account(id="acc_1", name="Account 1", currency="EUR", initial_balance=Decimal(35))
    acc_2 = Account(id="acc_2", name="Account 2", currency="RUB", initial_balance=Decimal(0))

    debit, credit = transfer(acc_1, acc_2, debit_amt=Decimal(10), credit_amt=Decimal(1000))

    assert acc_1.balance == Decimal(25)
    assert acc_2.balance == Decimal(1000)
