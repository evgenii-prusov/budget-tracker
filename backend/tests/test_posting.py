from app.model import Posting
from conftest import JAN_01
from conftest import JAN_02
from conftest import JAN_03


def test_posting_objects_sort_chronologically_by_date(
    posting_1: Posting, posting_2: Posting, posting_3: Posting
):
    # Arrange: Use posting fixtures with different dates
    # (posting_2 is Jan 02, posting_1 is Jan 01, posting_3 is Jan 03)

    # Act: Sort postings list
    postings = [posting_2, posting_1, posting_3]
    postings.sort()

    # Assert: Postings are sorted chronologically by date
    assert postings[0].posting_date == JAN_01
    assert postings[1].posting_date == JAN_02
    assert postings[2].posting_date == JAN_03
