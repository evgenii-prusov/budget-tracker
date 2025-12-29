from decimal import Decimal

from conftest import JAN_01
from conftest import JAN_02
from conftest import JAN_03


def test_entry_objects_sort_chronologically_by_date(make_entry):
    # Arrange: Create entries with different dates using factory
    entry_1 = make_entry(id="tx-1", entry_date=JAN_01, category="taxi")
    entry_2 = make_entry(
        id="tx-2", amount=Decimal(3), entry_date=JAN_02, category="food"
    )
    entry_3 = make_entry(
        id="tx-3",
        account_id="a-2",
        amount=Decimal(1),
        entry_date=JAN_03,
        category="taxi",
    )

    # Act: Sort entries list
    entries = [entry_2, entry_1, entry_3]
    entries.sort()

    # Assert: Entries are sorted chronologically by date
    assert entries[0].entry_date == JAN_01
    assert entries[1].entry_date == JAN_02
    assert entries[2].entry_date == JAN_03
