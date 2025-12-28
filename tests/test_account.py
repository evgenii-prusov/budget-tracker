import pytest
from decimal import Decimal
from datetime import date

from budget_tracker.model import Account
from budget_tracker.model import Entry
from budget_tracker.model import transfer
from budget_tracker.model import InsufficientFundsError

JAN_01_2025 = date.fromisoformat("2025-01-01")
JAN_02_2025 = date.fromisoformat("2025-01-02")
JAN_03_2025 = date.fromisoformat("2025-01-03")


def test_account_balance_is_sum_of_init_balance_and_entries(
    acc_eur: Account,
):
    acc_eur.record_entry(
        Decimal("2"), JAN_01_2025, category="TAXI", category_type="EXPENSE"
    )
    acc_eur.record_entry(
        Decimal("3"), JAN_01_2025, category="TRAVEL", category_type="EXPENSE"
    )
    acc_eur.record_entry(
        Decimal("500"),
        JAN_01_2025,
        category="KINDERGELD",
        category_type="INCOME",
    )

    assert acc_eur.balance == Decimal("530")


def test_transfer_with_different_currencies(
    acc_eur: Account, acc_rub: Account
):
    debit_entry, credit_entry = transfer(
        acc_eur,
        acc_rub,
        JAN_01_2025,
        debit_amt=Decimal(10),
        credit_amt=Decimal(1000),
    )

    assert acc_eur.balance == Decimal(25)
    assert acc_rub.balance == Decimal(1000)
    assert debit_entry.date == credit_entry.date


def test_entry_keeps_category(acc_eur: Account):
    acc_eur.record_entry(
        Decimal("3"),
        JAN_01_2025,
        "Taxi",
        category_type="EXPENSE",
    )
    assert acc_eur._entries.pop().category == "Taxi"


def test_entries_sorted_by_date():
    entry_2 = Entry(
        "tx-2", "a-1", Decimal("3"), JAN_02_2025, "food", "EXPENSE"
    )
    entry_1 = Entry(
        "tx-1", "a-1", Decimal("0"), JAN_01_2025, "taxi", "EXPENSE"
    )
    entry_3 = Entry(
        "tx-3", "a-2", Decimal("1"), JAN_03_2025, "taxi", "EXPENSE"
    )

    entries = [entry_2, entry_1, entry_3]
    entries.sort()
    assert entries[0].date == JAN_01_2025
    assert entries[1].date == JAN_02_2025
    assert entries[2].date == JAN_03_2025


def test_raise_insufficient_funds_error(acc_eur: Account):
    with pytest.raises(InsufficientFundsError):
        acc_eur.record_entry(
            Decimal("50"), JAN_01_2025, "some_category", "EXPENSE"
        )


def test_transfer_rejects_non_decimal_debit_amt(
    acc_eur: Account, acc_rub: Account
):
    with pytest.raises(TypeError) as exc_info:
        transfer(
            acc_eur,
            acc_rub,
            JAN_01_2025,
            debit_amt=10,  # int instead of Decimal
            credit_amt=Decimal(1000),
        )
    assert "debit_amt must be Decimal" in str(exc_info.value)
    assert "got int" in str(exc_info.value)
    assert "Use Decimal(str(value)) to convert" in str(exc_info.value)


def test_transfer_rejects_non_decimal_credit_amt(
    acc_eur: Account, acc_rub: Account
):
    with pytest.raises(TypeError) as exc_info:
        transfer(
            acc_eur,
            acc_rub,
            JAN_01_2025,
            debit_amt=Decimal(10),
            credit_amt=1000,  # int instead of Decimal
        )
    assert "credit_amt must be Decimal" in str(exc_info.value)
    assert "got int" in str(exc_info.value)
    assert "Use Decimal(str(value)) to convert" in str(exc_info.value)


def test_transfer_rejects_float_debit_amt(
    acc_eur: Account, acc_rub: Account
):
    with pytest.raises(TypeError) as exc_info:
        transfer(
            acc_eur,
            acc_rub,
            JAN_01_2025,
            debit_amt=10.5,  # float instead of Decimal
            credit_amt=Decimal(1000),
        )
    assert "debit_amt must be Decimal" in str(exc_info.value)
    assert "got float" in str(exc_info.value)


def test_transfer_rejects_string_credit_amt(
    acc_eur: Account, acc_rub: Account
):
    with pytest.raises(TypeError) as exc_info:
        transfer(
            acc_eur,
            acc_rub,
            JAN_01_2025,
            debit_amt=Decimal(10),
            credit_amt="1000",  # string instead of Decimal
        )
    assert "credit_amt must be Decimal" in str(exc_info.value)
    assert "got str" in str(exc_info.value)


def test_transfer_accepts_valid_decimals(
    acc_eur: Account, acc_rub: Account
):
    # This test ensures our validation doesn't break valid transfers
    debit_entry, credit_entry = transfer(
        acc_eur,
        acc_rub,
        JAN_01_2025,
        debit_amt=Decimal("10"),
        credit_amt=Decimal("1000"),
    )
    assert acc_eur.balance == Decimal(25)
    assert acc_rub.balance == Decimal(1000)
