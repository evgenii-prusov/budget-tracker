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


def test_entry_rejects_int_amount():
    with pytest.raises(TypeError, match="amount must be Decimal, got int"):
        Entry("id", "acc_id", 100, JAN_01_2025, "category", "EXPENSE")


def test_entry_rejects_float_amount():
    with pytest.raises(
        TypeError, match="amount must be Decimal, got float"
    ):
        Entry("id", "acc_id", 100.5, JAN_01_2025, "category", "EXPENSE")


def test_entry_rejects_string_amount():
    with pytest.raises(TypeError, match="amount must be Decimal, got str"):
        Entry("id", "acc_id", "100", JAN_01_2025, "category", "EXPENSE")


def test_account_rejects_int_initial_balance():
    with pytest.raises(
        TypeError, match="initial_balance must be Decimal, got int"
    ):
        Account(None, "Test Account", "EUR", 100)


def test_account_rejects_float_initial_balance():
    with pytest.raises(
        TypeError, match="initial_balance must be Decimal, got float"
    ):
        Account(None, "Test Account", "EUR", 100.5)


def test_account_rejects_string_initial_balance():
    with pytest.raises(
        TypeError, match="initial_balance must be Decimal, got str"
    ):
        Account(None, "Test Account", "EUR", "100")
