import pytest
from decimal import Decimal

from app.domain.model import Account
from app.domain.model import create_transfer
from app.domain.model import InsufficientFundsError
from app.domain.model import PostingType
from tests.constants import JAN_01


class TestCreateTransfer:
    """Tests for create_transfer() function."""

    def test_transfer_with_different_currencies(
        self, acc_eur: Account, acc_rub: Account
    ):
        # Arrange & Act: Transfer between EUR and RUB accounts
        transfer = create_transfer(
            acc_eur,
            acc_rub,
            JAN_01,
            debit_amount=Decimal(10),
            credit_amount=Decimal(1000),
        )

        # Assert: Both balances updated correctly
        assert acc_eur.balance == Decimal(25)
        assert acc_rub.balance == Decimal(1000)
        assert transfer.transfer_date == JAN_01

    def test_transfer_stores_description(self, acc_eur: Account, acc_rub: Account):
        # Arrange & Act: Create transfer with description
        transfer = create_transfer(
            acc_eur,
            acc_rub,
            JAN_01,
            debit_amount=Decimal(10),
            credit_amount=Decimal(1000),
            description="D1",
        )

        # Assert: Description is stored
        assert transfer.description == "D1"

    def test_transfer_raises_insufficient_funds(
        self, acc_eur: Account, acc_rub: Account
    ):
        # Arrange & Act: Attempt transfer exceeding balance
        with pytest.raises(InsufficientFundsError):
            create_transfer(
                acc_eur,
                acc_rub,
                JAN_01,
                debit_amount=Decimal(50),
                credit_amount=Decimal(5000),
            )

        # Assert: Balances unchanged after failed transfer
        assert acc_eur.balance == Decimal(35)
        assert acc_rub.balance == Decimal(0)

    @pytest.mark.parametrize(
        "debit_amount,credit_amount,expected_param,expected_type",
        [
            (10, Decimal(1000), "debit_amount", "int"),
            (Decimal(10), 1000, "credit_amount", "int"),
            (10.5, Decimal(1000), "debit_amount", "float"),
            (Decimal(10), "1000", "credit_amount", "str"),
        ],
        ids=["int-debit", "int-credit", "float-debit", "str-credit"],
    )
    def test_transfer_rejects_non_decimal_types_with_type_error(
        self,
        acc_eur: Account,
        acc_rub: Account,
        debit_amount,
        credit_amount,
        expected_param,
        expected_type,
    ):
        # Arrange & Act: Attempt transfer with invalid type
        with pytest.raises(TypeError) as exc_info:
            create_transfer(
                acc_eur,
                acc_rub,
                JAN_01,
                debit_amount=debit_amount,
                credit_amount=credit_amount,
            )

        # Assert: Verify error message content
        error_msg = str(exc_info.value)
        assert f"{expected_param} must be Decimal" in error_msg
        assert f"got {expected_type}" in error_msg
        assert "Use Decimal(str(value)) to convert" in error_msg

    def test_transfer_succeeds_with_valid_decimal_amounts(
        self, acc_eur: Account, acc_rub: Account
    ):
        # Arrange & Act: Transfer with valid Decimal amounts
        create_transfer(
            acc_eur,
            acc_rub,
            JAN_01,
            debit_amount=Decimal(10),
            credit_amount=Decimal(1000),
        )

        # Assert: Transfer succeeds with correct balances
        assert acc_eur.balance == Decimal(25)
        assert acc_rub.balance == Decimal(1000)


class TestRecordPosting:
    """Tests for Account.record_posting() method."""

    def test_record_posting_preserves_category_name(self, acc_eur: Account):
        # Arrange & Act: Record posting with custom category
        acc_eur.record_posting(
            Decimal(3), JAN_01, category="cat_1", posting_type=PostingType.EXPENSE
        )

        # Assert: Category name is preserved
        posting = acc_eur._postings[-1]
        assert posting.category == "cat_1"

    def test_record_posting_raises_insufficient_funds_when_balance_negative(
        self, acc_eur: Account
    ):
        # Arrange & Act: Attempt to record expense exceeding balance
        with pytest.raises(InsufficientFundsError):
            acc_eur.record_posting(
                Decimal(50), JAN_01, category="cat_1", posting_type=PostingType.EXPENSE
            )

    @pytest.mark.parametrize(
        "amount,expected_type",
        [
            (10, "int"),
            (10.5, "float"),
            ("10", "str"),
        ],
        ids=["int-amount", "float-amount", "str-amount"],
    )
    def test_record_posting_rejects_non_decimal_amounts_with_type_error(
        self, acc_eur: Account, amount, expected_type
    ):
        # Arrange & Act: Attempt to record posting with invalid amount type
        with pytest.raises(TypeError) as exc_info:
            acc_eur.record_posting(
                amount, JAN_01, category="cat_1", posting_type=PostingType.EXPENSE
            )

        # Assert: Verify error message content
        error_msg = str(exc_info.value)
        assert "amount must be Decimal" in error_msg
        assert f"got {expected_type}" in error_msg
        assert "Use Decimal(str(value)) to convert" in error_msg

    def test_record_posting_succeeds_with_valid_decimal_amount(self, acc_eur: Account):
        # Arrange & Act: Record posting with valid Decimal amount
        posting = acc_eur.record_posting(
            Decimal(10), JAN_01, category="cat_1", posting_type=PostingType.EXPENSE
        )

        # Assert: Posting recorded with correct values
        assert acc_eur.balance == Decimal(25)
        assert posting.amount == Decimal("-10")
