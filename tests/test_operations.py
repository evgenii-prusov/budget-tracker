import pytest
from decimal import Decimal

from budget_tracker.model import Account
from budget_tracker.model import transfer
from budget_tracker.model import InsufficientFundsError
from conftest import JAN_01


class TestTransfer:
    """Tests for transfer() function."""

    def test_transfer_with_different_currencies(
        self, acc_eur: Account, acc_rub: Account
    ):
        # Arrange & Act: Transfer between EUR and RUB accounts
        debit_entry, credit_entry = transfer(
            acc_eur,
            acc_rub,
            JAN_01,
            debit_amt=Decimal(10),
            credit_amt=Decimal(1000),
        )

        # Assert: Both balances updated correctly, dates match
        assert acc_eur.balance == Decimal(25)
        assert acc_rub.balance == Decimal(1000)
        assert debit_entry.entry_date == credit_entry.entry_date

    @pytest.mark.parametrize(
        "debit_amt,credit_amt,expected_param,expected_type",
        [
            (10, Decimal(1000), "debit_amt", "int"),
            (Decimal(10), 1000, "credit_amt", "int"),
            (10.5, Decimal(1000), "debit_amt", "float"),
            (Decimal(10), "1000", "credit_amt", "str"),
        ],
        ids=["int-debit", "int-credit", "float-debit", "str-credit"],
    )
    def test_transfer_rejects_non_decimal_types_with_type_error(
        self,
        acc_eur: Account,
        acc_rub: Account,
        debit_amt,
        credit_amt,
        expected_param,
        expected_type,
    ):
        # Arrange & Act: Attempt transfer with invalid type
        with pytest.raises(TypeError) as exc_info:
            transfer(
                acc_eur,
                acc_rub,
                JAN_01,
                debit_amt=debit_amt,  # type: ignore[arg-type]
                credit_amt=credit_amt,  # type: ignore[arg-type]
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
        debit_entry, credit_entry = transfer(
            acc_eur,
            acc_rub,
            JAN_01,
            debit_amt=Decimal("10"),
            credit_amt=Decimal("1000"),
        )

        # Assert: Transfer succeeds with correct balances
        assert acc_eur.balance == Decimal(25)
        assert acc_rub.balance == Decimal(1000)


class TestRecordEntry:
    """Tests for Account.record_entry() method."""

    def test_record_entry_preserves_category_name(self, acc_eur: Account):
        # Arrange & Act: Record entry with custom category
        acc_eur.record_entry(
            Decimal(3),
            JAN_01,
            "Taxi",
            category_type="EXPENSE",
        )

        # Assert: Category name is preserved
        assert acc_eur._entries.pop().category == "Taxi"

    def test_record_entry_raises_insufficient_funds_when_balance_negative(
        self, acc_eur: Account
    ):
        # Arrange & Act: Attempt to record expense exceeding balance
        with pytest.raises(InsufficientFundsError):
            acc_eur.record_entry(
                Decimal(50), JAN_01, "some_category", "EXPENSE"
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
    def test_record_entry_rejects_non_decimal_amounts_with_type_error(
        self, acc_eur: Account, amount, expected_type
    ):
        # Arrange & Act: Attempt to record entry with invalid amount type
        with pytest.raises(TypeError) as exc_info:
            acc_eur.record_entry(
                amount,  # type: ignore[arg-type]
                JAN_01,
                "TAXI",
                "EXPENSE",
            )

        # Assert: Verify error message content
        error_msg = str(exc_info.value)
        assert "amount must be Decimal" in error_msg
        assert f"got {expected_type}" in error_msg
        assert "Use Decimal(str(value)) to convert" in error_msg

    def test_record_entry_succeeds_with_valid_decimal_amount(
        self, acc_eur: Account
    ):
        # Arrange & Act: Record entry with valid Decimal amount
        entry = acc_eur.record_entry(Decimal(10), JAN_01, "TAXI", "EXPENSE")

        # Assert: Entry recorded with correct values
        assert acc_eur.balance == Decimal(25)
        assert entry.amount == Decimal("-10")
