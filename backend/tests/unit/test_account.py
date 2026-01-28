from decimal import Decimal

from app.domain.model import Account
from app.domain.model import PostingType
from app.domain.model import create_transfer
from tests.constants import JAN_01


def test_account_balance_is_sum_of_init_balance_and_postings(
    acc_eur: Account,
):
    # Arrange: Record multiple postings of different types
    acc_eur.record_posting(
        Decimal(2), JAN_01, category_id="CAT_1", posting_type=PostingType.EXPENSE
    )
    acc_eur.record_posting(
        Decimal(3), JAN_01, category_id="CAT_2", posting_type=PostingType.EXPENSE
    )
    acc_eur.record_posting(
        Decimal(500), JAN_01, category_id="CAT_3", posting_type=PostingType.INCOME
    )

    # Act: Get account balance
    balance = acc_eur.balance

    # Assert: Balance equals initial balance plus sum of postings
    # Initial: 35, Expenses: -5, Income: +500, Total: 530
    assert balance == Decimal(530)


def test_account_balance_reflects_transfers(acc_eur: Account, acc_rub: Account):
    # Arrange:
    # acc_eur initial: 35
    # acc_rub initial: 0

    # Act: Create transfers
    # 1. Outgoing from EUR to RUB: 10 EUR
    create_transfer(
        source=acc_eur,
        dest=acc_rub,
        transfer_date=JAN_01,
        debit_amount=Decimal(10),
        credit_amount=Decimal(800),  # Example cross-currency
    )

    # 2. Incoming to EUR from RUB: 5 EUR
    create_transfer(
        source=acc_rub,
        dest=acc_eur,
        transfer_date=JAN_01,
        debit_amount=Decimal(400),
        credit_amount=Decimal(5),
    )

    # Assert:
    # acc_eur balance: 35 - 10 + 5 = 30
    # acc_rub balance: 0 + 800 - 400 = 400
    assert acc_eur.balance == Decimal(30)
    assert acc_rub.balance == Decimal(400)
