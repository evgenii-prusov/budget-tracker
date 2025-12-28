from decimal import Decimal
from datetime import date

from budget_tracker.model import Entry

JAN_01_2025 = date.fromisoformat("2025-01-01")
JAN_02_2025 = date.fromisoformat("2025-01-02")
JAN_03_2025 = date.fromisoformat("2025-01-03")


def test_entry_objects_sort_chronologically_by_date():
    # Arrange: Create entries with different dates
    entry_2 = Entry("tx-2", "a-1", Decimal(3), JAN_02_2025, "food", "EXPENSE")
    entry_1 = Entry("tx-1", "a-1", Decimal(0), JAN_01_2025, "taxi", "EXPENSE")
    entry_3 = Entry("tx-3", "a-2", Decimal(1), JAN_03_2025, "taxi", "EXPENSE")

    # Act: Sort entries list
    entries = [entry_2, entry_1, entry_3]
    entries.sort()

    # Assert: Entries are sorted chronologically by date
    assert entries[0].date == JAN_01_2025
    assert entries[1].date == JAN_02_2025
    assert entries[2].date == JAN_03_2025
