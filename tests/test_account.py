from decimal import Decimal

from budget_tracker.model import Account
from conftest import JAN_01


def test_account_balance_is_sum_of_init_balance_and_entries(
    acc_eur: Account,
):
    # Arrange: Record multiple entries of different types
    acc_eur.record_entry(
        Decimal(2), JAN_01, category="TAXI", category_type="EXPENSE"
    )
    acc_eur.record_entry(
        Decimal(3), JAN_01, category="TRAVEL", category_type="EXPENSE"
    )
    acc_eur.record_entry(
        Decimal(500), JAN_01, category="KINDERGELD", category_type="INCOME"
    )

    # Act: Get account balance
    balance = acc_eur.balance

    # Assert: Balance equals initial balance plus sum of entries
    # Initial: 35, Expenses: -5, Income: +500, Total: 530
    assert balance == Decimal(530)
