from app.model import Entry
from conftest import JAN_01
from conftest import JAN_02
from conftest import JAN_03


def test_entry_objects_sort_chronologically_by_date(
    entry_1: Entry, entry_2: Entry, entry_3: Entry
):
    # Arrange: Use entry fixtures with different dates
    # (entry_2 is Jan 02, entry_1 is Jan 01, entry_3 is Jan 03)

    # Act: Sort entries list
    entries = [entry_2, entry_1, entry_3]
    entries.sort()

    # Assert: Entries are sorted chronologically by date
    assert entries[0].entry_date == JAN_01
    assert entries[1].entry_date == JAN_02
    assert entries[2].entry_date == JAN_03
