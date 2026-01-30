from sqlalchemy import text
from decimal import Decimal
from datetime import date
from app.adapters import repository
from app.domain.model import Account, PostingType, Category, Transfer
from tests.constants import JAN_01


def test_repository_save_an_account(session, acc_eur, acc_rub):
    repo = repository.SqlAlchemyRepository(session)
    repo.add(acc_eur)
    repo.add(acc_rub)
    session.commit()

    rows = set(
        session.execute(
            text("SELECT account_id, name, currency, initial_balance FROM account")
        )
    )
    assert rows == {
        (acc_eur.account_id, acc_eur.name, acc_eur.currency, acc_eur.initial_balance),
        (acc_rub.account_id, acc_rub.name, acc_rub.currency, acc_rub.initial_balance),
    }


def test_repository_retrieve_account_with_postings(session):
    session.execute(
        text(
            "INSERT INTO account (account_id, name, currency, initial_balance)"
            "VALUES ('1', 'rub', 'RUB', 100)"
        )
    )
    session.execute(
        text(
            "INSERT INTO posting "
            "(posting_id, account_id, amount, posting_date, category_id, posting_type)"
            "VALUES ('1', '1', 100, '2025-12-26', NULL, 'INCOME')"
        )
    )
    session.commit()

    repo = repository.SqlAlchemyRepository(session)
    account = repo.get("1")
    from decimal import Decimal

    assert account == Account(
        account_id="1", name="rub", currency="RUB", initial_balance=Decimal(100)
    )
    assert account.balance == 200


def test_repository_get_nonexistent_account_returns_none(session):
    # 1. Arrange: Empty database, no accounts
    repo = repository.SqlAlchemyRepository(session)

    # 2. Act: Try to get nonexistent account
    account = repo.get("nonexistent-id")

    # 3. Assert: Returns None, not an exception
    assert account is None


def test_repository_retrieve_all_accounts(session):
    session.execute(
        text(
            "INSERT INTO account (account_id, name, currency, initial_balance) VALUES"
            " ('1', 'rub', 'RUB', 100),"
            " ('2', 'eur', 'EUR', 200)"
        )
    )

    session.commit()

    repo = repository.SqlAlchemyRepository(session)
    accounts = repo.list_all()
    assert accounts == [
        Account(
            account_id="2", name="eur", currency="EUR", initial_balance=Decimal(200)
        ),
        Account(
            account_id="1", name="rub", currency="RUB", initial_balance=Decimal(100)
        ),
    ]


def test_repository_delete_account_does_not_cascade_postings(session):
    """Deleting account should not cascade-delete postings."""
    # Arrange: Create account with posting via ORM
    account = Account("acc-1", "Test", "USD", Decimal(100))
    account.record_posting(
        Decimal(10),
        date(2025, 1, 1),
        category_id=None,
        posting_type=PostingType.EXPENSE,
    )
    session.add(account)
    session.commit()

    # Verify both exist in database (raw SQL, bypasses ORM cache)
    account_count = session.execute(text("SELECT COUNT(*) FROM account")).scalar()
    posting_count = session.execute(text("SELECT COUNT(*) FROM posting")).scalar()
    assert account_count == 1
    assert posting_count == 1

    # Act: Delete via repository
    repo = repository.SqlAlchemyRepository(session)
    loaded_account = repo.get("acc-1")
    repo.delete(loaded_account)
    session.commit()

    # Assert: Account is gone, postings remain
    account_count = session.execute(text("SELECT COUNT(*) FROM account")).scalar()
    posting_count = session.execute(text("SELECT COUNT(*) FROM posting")).scalar()
    assert account_count == 0
    assert posting_count == 1


def test_list_postings_empty(session):
    repo = repository.SqlAlchemyRepository(session)
    assert repo.list_postings() == []


def test_list_postings_returns_all(session):
    repo = repository.SqlAlchemyRepository(session)
    account = Account("a1", "Test", "EUR", Decimal(100))
    repo.add(account)
    account.record_posting(
        Decimal(10), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
    )
    session.commit()

    postings = repo.list_postings()

    assert len(postings) == 1


def test_list_postings_filtered_by_account(session):
    repo = repository.SqlAlchemyRepository(session)
    a1 = Account("a1", "Test1", "EUR", Decimal(100))
    a2 = Account("a2", "Test2", "EUR", Decimal(100))
    repo.add(a1)
    repo.add(a2)
    a1.record_posting(
        Decimal(10), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
    )
    a2.record_posting(
        Decimal(20), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
    )
    session.commit()

    postings = repo.list_postings(account_id="a1")

    assert len(postings) == 1
    assert postings[0].account_id == "a1"


def test_repository_pagination(session):
    repo = repository.SqlAlchemyRepository(session)
    for i in range(10):
        repo.add(Account(f"id-{i}", f"Acc {i}", "USD", Decimal(0)))
    session.commit()

    # Test limit
    page1 = repo.list_all(limit=3)
    assert len(page1) == 3
    assert page1[0].name == "Acc 0"

    # Test offset
    page2 = repo.list_all(skip=3, limit=3)
    assert len(page2) == 3
    assert page2[0].name == "Acc 3"


def test_list_postings_pagination_orders_by_date(session):
    repo = repository.SqlAlchemyRepository(session)
    account = Account("a1", "Test", "EUR", Decimal(100))
    repo.add(account)
    account.record_posting(
        Decimal(10), date(2025, 1, 1), category_id=None, posting_type=PostingType.EXPENSE
    )
    account.record_posting(
        Decimal(20), date(2025, 1, 2), category_id=None, posting_type=PostingType.EXPENSE
    )
    account.record_posting(
        Decimal(30), date(2025, 1, 3), category_id=None, posting_type=PostingType.EXPENSE
    )
    session.commit()

    page = repo.list_postings(skip=1, limit=1)
    assert len(page) == 1
    assert page[0].posting_date == date(2025, 1, 2)


def test_list_categories_pagination(session):
    repo = repository.SqlAlchemyRepository(session)
    repo.add_category(Category("c1", "Alpha"))
    repo.add_category(Category("c2", "Beta"))
    repo.add_category(Category("c3", "Gamma"))
    session.commit()

    page = repo.list_categories(skip=1, limit=1)
    assert len(page) == 1
    assert page[0].name == "Beta"


def test_list_transfers_pagination_orders_by_date(session):
    repo = repository.SqlAlchemyRepository(session)
    acc1 = Account("a1", "Source", "EUR", Decimal(100))
    acc2 = Account("a2", "Dest", "EUR", Decimal(0))
    repo.add(acc1)
    repo.add(acc2)
    repo.add_transfer(
        Transfer(
            "t1",
            acc1.account_id,
            acc2.account_id,
            Decimal(10),
            Decimal(10),
            date(2025, 1, 1),
        )
    )
    repo.add_transfer(
        Transfer(
            "t2",
            acc1.account_id,
            acc2.account_id,
            Decimal(20),
            Decimal(20),
            date(2025, 1, 2),
        )
    )
    repo.add_transfer(
        Transfer(
            "t3",
            acc1.account_id,
            acc2.account_id,
            Decimal(30),
            Decimal(30),
            date(2025, 1, 3),
        )
    )
    session.commit()

    page = repo.list_transfers(skip=1, limit=1)
    assert len(page) == 1
    assert page[0].transfer_date == date(2025, 1, 2)


def test_count_postings_for_account(session):
    repo = repository.SqlAlchemyRepository(session)
    account = Account("acc-count", "Count Test", "USD", Decimal(0))
    repo.add(account)

    # Add 3 postings
    for i in range(3):
        account.record_posting(
            Decimal(10), JAN_01, category_id=None, posting_type=PostingType.INCOME
        )
    session.commit()

    count = repo.count_postings_for_account("acc-count")
    assert count == 3

    count_empty = repo.count_postings_for_account("non-existent")
    assert count_empty == 0


def test_count_transfers_for_account(session):
    repo = repository.SqlAlchemyRepository(session)
    acc1 = Account("a1", "Source", "EUR", Decimal(100))
    acc2 = Account("a2", "Dest", "EUR", Decimal(0))
    repo.add(acc1)
    repo.add(acc2)
    repo.add_transfer(
        Transfer(
            "t1",
            acc1.account_id,
            acc2.account_id,
            Decimal(10),
            Decimal(10),
            date(2025, 1, 1),
        )
    )
    repo.add_transfer(
        Transfer(
            "t2",
            acc2.account_id,
            acc1.account_id,
            Decimal(5),
            Decimal(5),
            date(2025, 1, 2),
        )
    )
    session.commit()

    count = repo.count_transfers_for_account("a1")
    assert count == 2

    count_empty = repo.count_transfers_for_account("missing")
    assert count_empty == 0
