from decimal import Decimal

from budget_tracker.model import Account
from budget_tracker.model import Transaction


def test_account_balance_is_sum_of_initial_balance_and_transactions():
    acc_1 = Account(id='acc1', name="Account 1", currency="EUR", initial_balance=Decimal(35))
    acc_1.record_transaction(Decimal("-2"))
    acc_1.record_transaction(Decimal("-3"))
    assert acc_1.balance == Decimal("30")
