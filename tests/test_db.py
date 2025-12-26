from decimal import Decimal
from sqlalchemy import select, text

from budget_tracker.model import Account


def test_account_mapper_loads_accounts(session):
    session.execute(
        text(
            "INSERT INTO account (id, name, currency, initial_balance) VALUES "
            '("acc-1", "Revolut 1", "EUR", "25"),'
            '("acc-2", "Revolut 2",  "EUR", "0"),'
            '("acc-3", "Sparkasse",    "EUR", "100")'
        )
    )
    expected: set[Account] = {
        Account("acc-1", "Revolut 1", "EUR", Decimal("25")),
        Account("acc-2", "Revolut 2", "EUR", Decimal("0")),
        Account("acc-3", "Sparkasse", "EUR", Decimal("100")),
    }
    assert set(session.execute(select(Account)).scalars().all()) == expected


def test_account_mapper_saves_account(session, acc_eur):
    session.add(acc_eur)
    session.commit()

    rows = session.execute(select(Account)).scalars().all()
    assert len(rows) == 1
    assert rows[0] == acc_eur
