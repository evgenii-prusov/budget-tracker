import pytest
from sqlalchemy import text
from decimal import Decimal
from datetime import date
from app.adapters.account_repository import SqlAlchemyAccountRepository
from app.adapters.transfer_repository import SqlAlchemyTransferRepository
from app.adapters.category_repository import SqlAlchemyCategoryRepository
from app.domain.model import Account, CategoryType, PostingType, Category, Transfer
from tests.constants import JAN_01


def test_repository_save_an_account(session, acc_eur, acc_rub):
    repo = SqlAlchemyAccountRepository(session)
    repo.add(acc_eur)
    repo.add(acc_rub)
    session.commit()

    rows = set(
        session.execute(text("SELECT account_id, name, currency, initial_balance FROM account"))
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

    repo = SqlAlchemyAccountRepository(session)
    account = repo.get("1")
    assert account is not None

    assert account == Account(
        account_id="1", name="rub", currency="RUB", initial_balance=Decimal(100)
    )
    assert account.balance == 200


def test_repository_get_nonexistent_account_returns_none(session):
    repo = SqlAlchemyAccountRepository(session)
    account = repo.get("nonexistent-id")
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

    repo = SqlAlchemyAccountRepository(session)
    accounts = repo.list_all()
    assert accounts == [
        Account(account_id="2", name="eur", currency="EUR", initial_balance=Decimal(200)),
        Account(account_id="1", name="rub", currency="RUB", initial_balance=Decimal(100)),
    ]


def test_list_all_balance_uses_eager_loading(session):
    """list_all() must eager-load relationships so Account.balance works on detached objects.

    After expunging (truly detaching) all objects from the session, accessing balance
    would raise DetachedInstanceError if relationships had not been eagerly loaded.
    """
    repo = SqlAlchemyAccountRepository(session)
    account = Account("bal-1", "Eager Test", "EUR", Decimal(100))
    repo.add(account)
    account.record_posting(Decimal(30), JAN_01, category_id=None, posting_type=PostingType.INCOME)
    session.commit()

    accounts = repo.list_all()
    session.expunge_all()  # detach all objects; lazy loads would now raise DetachedInstanceError

    assert len(accounts) == 1
    assert accounts[0].balance == Decimal(130)


def test_get_balance_uses_eager_loading(session):
    """get() must eager-load relationships so Account.balance works on detached objects.

    After expunging (truly detaching) the object from the session, accessing balance
    would raise DetachedInstanceError if relationships had not been eagerly loaded.
    """
    repo = SqlAlchemyAccountRepository(session)
    account = Account("bal-2", "Eager Get Test", "EUR", Decimal(50))
    repo.add(account)
    account.record_posting(Decimal(20), JAN_01, category_id=None, posting_type=PostingType.INCOME)
    session.commit()

    loaded = repo.get("bal-2")
    assert loaded is not None
    session.expunge_all()  # detach all objects; lazy loads would now raise DetachedInstanceError

    assert loaded.balance == Decimal(70)


def test_repository_delete_account_deletes_postings_due_to_cascade(session):
    """Deleting an account that still has postings succeeds because of cascade delete."""
    from sqlalchemy import select

    account = Account("acc-1", "Test", "USD", Decimal(100))
    account.record_posting(
        Decimal(10),
        date(2025, 1, 1),
        category_id=None,
        posting_type=PostingType.EXPENSE,
    )
    session.add(account)
    session.commit()

    repo = SqlAlchemyAccountRepository(session)
    loaded_account = repo.get("acc-1")
    repo.delete(loaded_account)
    session.commit()

    # Verify both account and postings are gone
    assert repo.get("acc-1") is None
    from app.adapters.orm import postings

    assert session.execute(select(postings).where(postings.c.account_id == "acc-1")).all() == []


def test_repository_get_by_posting_id(session):
    account = Account("a1", "Test", "EUR", Decimal(100))
    session.add(account)
    posting = account.record_posting(
        Decimal(10), JAN_01, category_id=None, posting_type=PostingType.EXPENSE
    )
    session.commit()

    repo = SqlAlchemyAccountRepository(session)
    found = repo.get_by_posting_id(posting.posting_id)
    assert found is not None
    assert found.account_id == "a1"

    not_found = repo.get_by_posting_id("nonexistent")
    assert not_found is None


def test_list_postings_via_account(session):
    repo = SqlAlchemyAccountRepository(session)
    account = Account("a1", "Test", "EUR", Decimal(100))
    repo.add(account)
    account.record_posting(Decimal(10), JAN_01, category_id=None, posting_type=PostingType.EXPENSE)
    session.commit()

    loaded = repo.get("a1")
    assert loaded is not None
    assert len(loaded.postings) == 1


def test_list_postings_filtered_by_account(session):
    repo = SqlAlchemyAccountRepository(session)
    a1 = Account("a1", "Test1", "EUR", Decimal(100))
    a2 = Account("a2", "Test2", "EUR", Decimal(100))
    repo.add(a1)
    repo.add(a2)
    a1.record_posting(Decimal(10), JAN_01, category_id=None, posting_type=PostingType.EXPENSE)
    a2.record_posting(Decimal(20), JAN_01, category_id=None, posting_type=PostingType.EXPENSE)
    session.commit()

    loaded_a1 = repo.get("a1")
    assert loaded_a1 is not None
    assert len(loaded_a1.postings) == 1
    assert loaded_a1.postings[0].account_id == "a1"


def test_repository_pagination(session):
    repo = SqlAlchemyAccountRepository(session)
    for i in range(10):
        repo.add(Account(f"id-{i}", f"Acc {i}", "USD", Decimal(0)))
    session.commit()

    page1 = repo.list_all(limit=3)
    assert len(page1) == 3
    assert page1[0].name == "Acc 0"

    page2 = repo.list_all(skip=3, limit=3)
    assert len(page2) == 3
    assert page2[0].name == "Acc 3"


def test_list_categories_pagination(session):
    repo = SqlAlchemyCategoryRepository(session)
    repo.add(Category("c1", "Alpha", CategoryType.EXPENSE))
    repo.add(Category("c2", "Beta", CategoryType.EXPENSE))
    repo.add(Category("c3", "Gamma", CategoryType.EXPENSE))
    session.commit()

    page = repo.list_all(skip=1, limit=1)
    assert len(page) == 1
    assert page[0].name == "Beta"


def test_list_transfers_pagination_orders_by_date(session):
    account_repo = SqlAlchemyAccountRepository(session)
    transfer_repo = SqlAlchemyTransferRepository(session)
    acc1 = Account("a1", "Source", "EUR", Decimal(100))
    acc2 = Account("a2", "Dest", "EUR", Decimal(0))
    account_repo.add(acc1)
    account_repo.add(acc2)
    transfer_repo.add(
        Transfer(
            "t1",
            acc1.account_id,
            acc2.account_id,
            Decimal(10),
            Decimal(10),
            date(2025, 1, 1),
        )
    )
    transfer_repo.add(
        Transfer(
            "t2",
            acc1.account_id,
            acc2.account_id,
            Decimal(20),
            Decimal(20),
            date(2025, 1, 2),
        )
    )
    transfer_repo.add(
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

    page = transfer_repo.list_all(skip=1, limit=1)
    assert len(page) == 1
    assert page[0].transfer_date == date(2025, 1, 2)


def test_account_posting_count(session):
    repo = SqlAlchemyAccountRepository(session)
    account = Account("acc-count", "Count Test", "USD", Decimal(0))
    repo.add(account)

    for i in range(3):
        account.record_posting(
            Decimal(10), JAN_01, category_id=None, posting_type=PostingType.INCOME
        )
    session.commit()

    loaded = repo.get("acc-count")
    assert loaded is not None
    assert loaded.posting_count == 3


def test_account_transfer_count(session):
    account_repo = SqlAlchemyAccountRepository(session)
    transfer_repo = SqlAlchemyTransferRepository(session)
    acc1 = Account("a1", "Source", "EUR", Decimal(100))
    acc2 = Account("a2", "Dest", "EUR", Decimal(0))
    account_repo.add(acc1)
    account_repo.add(acc2)
    transfer_repo.add(
        Transfer(
            "t1",
            acc1.account_id,
            acc2.account_id,
            Decimal(10),
            Decimal(10),
            date(2025, 1, 1),
        )
    )
    transfer_repo.add(
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

    loaded = account_repo.get("a1")
    assert loaded is not None
    assert loaded.transfer_count == 2


def test_list_parents_eager_loads_children(session):
    """list_parents() must eagerly load children so .children works on detached objects."""
    repo = SqlAlchemyCategoryRepository(session)
    parent = Category("p1", "Food", CategoryType.EXPENSE)
    child = Category("c1", "Restaurants", CategoryType.EXPENSE, parent_id="p1")
    repo.add(parent)
    repo.add(child)
    session.commit()

    parents = repo.list_parents()
    session.expunge_all()  # detach; lazy loads would raise DetachedInstanceError

    assert len(parents) == 1
    assert len(parents[0].children) == 1  # fails before selectinload fix


def test_two_root_categories_same_name_raises_integrity_error(session):
    """Database must reject two root categories with the same name."""
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy import text

    ins = "INSERT INTO category (category_id, name, category_type) VALUES"
    with pytest.raises(IntegrityError):
        session.execute(text(f"{ins} ('r1', 'Food', 'EXPENSE')"))
        session.execute(text(f"{ins} ('r2', 'Food', 'EXPENSE')"))
        session.commit()


def test_list_parents_returns_only_root_categories(session):
    repo = SqlAlchemyCategoryRepository(session)
    parent = Category("p1", "Food", CategoryType.EXPENSE)
    child = Category("c1", "Restaurants", CategoryType.EXPENSE, parent_id="p1")
    repo.add(parent)
    repo.add(child)
    session.commit()

    parents = repo.list_parents()
    assert len(parents) == 1
    assert parents[0].category_id == "p1"


def test_list_children_returns_subcategories(session):
    repo = SqlAlchemyCategoryRepository(session)
    parent = Category("p1", "Food", CategoryType.EXPENSE)
    child1 = Category("c1", "Restaurants", CategoryType.EXPENSE, parent_id="p1")
    child2 = Category("c2", "Groceries", CategoryType.EXPENSE, parent_id="p1")
    repo.add(parent)
    repo.add(child1)
    repo.add(child2)
    session.commit()

    children = repo.list_children("p1")
    assert len(children) == 2
    assert {c.category_id for c in children} == {"c1", "c2"}

    assert repo.list_children("nonexistent") == []


def test_count_children(session):
    repo = SqlAlchemyCategoryRepository(session)
    parent = Category("p1", "Food", CategoryType.EXPENSE)
    child = Category("c1", "Restaurants", CategoryType.EXPENSE, parent_id="p1")
    repo.add(parent)
    repo.add(child)
    session.commit()

    assert repo.count_children("p1") == 1
    assert repo.count_children("nonexistent") == 0


def test_get_by_name_scoped_to_parent(session):
    repo = SqlAlchemyCategoryRepository(session)
    root = Category("p1", "Food", CategoryType.EXPENSE)
    child = Category("c1", "Snacks", CategoryType.EXPENSE, parent_id="p1")
    repo.add(root)
    repo.add(child)
    session.commit()

    # Root category found by name with parent_id=None
    assert repo.get_by_name("Food", parent_id=None) is not None
    # Subcategory found when scoped to parent
    assert repo.get_by_name("Snacks", parent_id="p1") is not None
    # Cross-scope lookups return None
    assert repo.get_by_name("Food", parent_id="p1") is None
    assert repo.get_by_name("Snacks", parent_id=None) is None


def test_category_count_postings(session):
    account_repo = SqlAlchemyAccountRepository(session)
    category_repo = SqlAlchemyCategoryRepository(session)

    cat = Category("cat-1", "Food", CategoryType.EXPENSE)
    category_repo.add(cat)
    account = Account("a1", "Test", "EUR", Decimal(100))
    account_repo.add(account)
    account.record_posting(
        Decimal(10), JAN_01, category_id="cat-1", posting_type=PostingType.EXPENSE
    )
    account.record_posting(
        Decimal(5), JAN_01, category_id="cat-1", posting_type=PostingType.EXPENSE
    )
    session.commit()

    assert category_repo.count_postings("cat-1") == 2
    assert category_repo.count_postings("nonexistent") == 0
