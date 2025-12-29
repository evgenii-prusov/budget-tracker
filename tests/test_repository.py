from sqlalchemy import text
from decimal import Decimal
from budget_tracker import repository
from budget_tracker.model import Account


def test_repository_save_an_account(session, acc_eur, acc_rub):
    repo = repository.SqlAlchemyRepository(session)
    repo.add(acc_eur)
    repo.add(acc_rub)
    session.commit()

    rows = set(
        session.execute(
            text("SELECT id, name, currency, initial_balance FROM account")
        )
    )
    assert rows == {
        (acc_eur.id, acc_eur.name, acc_eur.currency, acc_eur.initial_balance),
        (acc_rub.id, acc_rub.name, acc_rub.currency, acc_rub.initial_balance),
    }


def test_repository_retrieve_account_with_transactions(session):
    session.execute(
        text(
            "INSERT INTO account (id, name, currency, initial_balance)"
            "VALUES ('1', 'rub', 'RUB', 100)"
        )
    )
    session.execute(
        text(
            "INSERT INTO entry "
            "(id, account_id, amount, entry_date, category, category_type)"
            "VALUES ('1', '1', 100, '2025-12-26', 'rub', 'INCOME')"
        )
    )
    session.commit()

    repo = repository.SqlAlchemyRepository(session)
    account = repo.get("1")
    from decimal import Decimal

    assert account == Account(
        id="1", name="rub", currency="RUB", initial_balance=Decimal(100)
    )
    assert account.balance == 200


def test_repository_retrieve_all_accounts(session):
    session.execute(
        text(
            "INSERT INTO account (id, name, currency, initial_balance) VALUES"
            " ('1', 'rub', 'RUB', 100),"
            " ('2', 'eur', 'EUR', 200)"
        )
    )

    session.commit()

    repo = repository.SqlAlchemyRepository(session)
    accounts = repo.list_all()
    assert accounts == [
        Account(
            id="1", name="rub", currency="RUB", initial_balance=Decimal(100)
        ),
        Account(
            id="2", name="eur", currency="EUR", initial_balance=Decimal(200)
        ),
    ]
