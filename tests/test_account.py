from decimal import Decimal
from datetime import date

from budget_tracker.model import Account

JAN_01_2025 = date.fromisoformat("2025-01-01")


def test_account_balance_is_sum_of_init_balance_and_entries(
    acc_eur: Account,
):
    # Arrange: Record multiple entries of different types
    acc_eur.record_entry(
        Decimal(2), JAN_01_2025, category="TAXI", category_type="EXPENSE"
    )
    acc_eur.record_entry(
        Decimal(3), JAN_01_2025, category="TRAVEL", category_type="EXPENSE"
    )
    acc_eur.record_entry(
        Decimal(500),
        JAN_01_2025,
        category="KINDERGELD",
        category_type="INCOME",
    )

    # Act: Get account balance
    balance = acc_eur.balance

    # Assert: Balance equals initial balance plus sum of entries
    # Initial: 35, Expenses: -5, Income: +500, Total: 530
    assert balance == Decimal(530)
