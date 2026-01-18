from decimal import Decimal

from app.model import Account
from app.model import CategoryType
from conftest import JAN_01


def test_account_balance_is_sum_of_init_balance_and_postings(
    acc_eur: Account,
):
    # Arrange: Record multiple postings of different types
    acc_eur.record_posting(
        Decimal(2), JAN_01, category="TAXI", category_type=CategoryType.EXPENSE
    )
    acc_eur.record_posting(
        Decimal(3),
        JAN_01,
        category="TRAVEL",
        category_type=CategoryType.EXPENSE,
    )
    acc_eur.record_posting(
        Decimal(500),
        JAN_01,
        category="KINDERGELD",
        category_type=CategoryType.INCOME,
    )

    # Act: Get account balance
    balance = acc_eur.balance

    # Assert: Balance equals initial balance plus sum of postings
    # Initial: 35, Expenses: -5, Income: +500, Total: 530
    assert balance == Decimal(530)
