from sqlalchemy import text
from budget_tracker import repository


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
