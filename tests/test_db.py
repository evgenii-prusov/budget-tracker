from decimal import Decimal
from sqlalchemy import text

from budget_tracker.model import Account


def test_accounts_mapper_can_load_accounts(session):
    session.execute(
        text(
            "INSERT INTO account (id, name, currency, initial_balance) VALUES "
            '("acc-1", "Revolut Женя", "EUR", "25"),'
            '("acc-2", "Revolut Яна",  "EUR", "0"),'
            '("acc-3", "Sparkasse",    "EUR", "100")'
        )
    )
    expected: set[Account] = {
        Account("acc-1", "Revolut Женя", "EUR", Decimal("25")),
        Account("acc-2", "Revolut Яна", "EUR", Decimal("0")),
        Account("acc-3", "Sparkasse", "EUR", Decimal("100")),
    }
    assert set(session.query(Account).all()) == expected
