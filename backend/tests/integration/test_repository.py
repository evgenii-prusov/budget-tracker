from sqlalchemy import text
from decimal import Decimal
from datetime import date
from app.adapters import repository
from app.domain.model import Account, PostingType


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
            "(posting_id, account_id, amount, posting_date, category, posting_type)"
            "VALUES ('1', '1', 100, '2025-12-26', 'rub', 'INCOME')"
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
            account_id="1", name="rub", currency="RUB", initial_balance=Decimal(100)
        ),
        Account(
            account_id="2", name="eur", currency="EUR", initial_balance=Decimal(200)
        ),
    ]


def test_repository_delete_account_cascades_postings(session):
    """Verify ORM cascade configuration: deleting account also deletes postings."""
    # Arrange: Create account with posting via ORM
    account = Account("acc-1", "Test", "USD", Decimal(100))
    account.record_posting(
        Decimal(10),
        date(2025, 1, 1),
        category="food",
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

    # Assert: Both account AND posting are gone (raw SQL verification)
    account_count = session.execute(text("SELECT COUNT(*) FROM account")).scalar()
    posting_count = session.execute(text("SELECT COUNT(*) FROM posting")).scalar()
    assert account_count == 0
    assert posting_count == 0  # Cascade delete worked
