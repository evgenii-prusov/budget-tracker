"""Seed the development database with sample data.

Usage:
    uv run python -m scripts.seed

Wipes all existing data and inserts a curated dataset of accounts,
categories, postings, and transfers for manual testing.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.core.db import Database
from app.domain.model import (
    Account,
    Category,
    Transfer,
    PostingType,
)

ACCOUNTS = [
    ("Checking", "USD", Decimal("5000")),
    ("Savings", "EUR", Decimal("10000")),
    ("Cash", "RUB", Decimal("25000")),
    ("Travel Fund", "GBP", Decimal("1500")),
]

CATEGORIES = [
    "Groceries",
    "Rent",
    "Salary",
    "Dining Out",
    "Transport",
    "Utilities",
    "Entertainment",
    "Freelance",
]

# (account_name, amount, date, category_name, posting_type)
POSTINGS = [
    # January salaries / freelance
    ("Checking", Decimal("3500"), date(2026, 1, 5), "Salary", PostingType.INCOME),
    ("Checking", Decimal("800"), date(2026, 1, 20), "Freelance", PostingType.INCOME),
    ("Savings", Decimal("2000"), date(2026, 1, 10), "Freelance", PostingType.INCOME),
    # January expenses
    ("Checking", Decimal("1200"), date(2026, 1, 1), "Rent", PostingType.EXPENSE),
    ("Checking", Decimal("85"), date(2026, 1, 3), "Groceries", PostingType.EXPENSE),
    ("Checking", Decimal("45"), date(2026, 1, 7), "Dining Out", PostingType.EXPENSE),
    ("Checking", Decimal("30"), date(2026, 1, 8), "Transport", PostingType.EXPENSE),
    ("Checking", Decimal("120"), date(2026, 1, 12), "Utilities", PostingType.EXPENSE),
    ("Checking", Decimal("60"), date(2026, 1, 14), "Entertainment", PostingType.EXPENSE),
    ("Checking", Decimal("95"), date(2026, 1, 18), "Groceries", PostingType.EXPENSE),
    ("Checking", Decimal("35"), date(2026, 1, 22), "Dining Out", PostingType.EXPENSE),
    ("Checking", Decimal("25"), date(2026, 1, 25), "Transport", PostingType.EXPENSE),
    ("Cash", Decimal("1500"), date(2026, 1, 6), "Groceries", PostingType.EXPENSE),
    ("Cash", Decimal("800"), date(2026, 1, 15), "Entertainment", PostingType.EXPENSE),
    ("Cash", Decimal("2000"), date(2026, 1, 28), "Transport", PostingType.EXPENSE),
    # February salaries / freelance
    ("Checking", Decimal("3500"), date(2026, 2, 5), "Salary", PostingType.INCOME),
    ("Checking", Decimal("600"), date(2026, 2, 18), "Freelance", PostingType.INCOME),
    # February expenses
    ("Checking", Decimal("1200"), date(2026, 2, 1), "Rent", PostingType.EXPENSE),
    ("Checking", Decimal("90"), date(2026, 2, 2), "Groceries", PostingType.EXPENSE),
    ("Checking", Decimal("55"), date(2026, 2, 6), "Dining Out", PostingType.EXPENSE),
    ("Checking", Decimal("40"), date(2026, 2, 9), "Transport", PostingType.EXPENSE),
    ("Checking", Decimal("110"), date(2026, 2, 11), "Utilities", PostingType.EXPENSE),
    ("Checking", Decimal("75"), date(2026, 2, 13), "Entertainment", PostingType.EXPENSE),
    ("Checking", Decimal("100"), date(2026, 2, 16), "Groceries", PostingType.EXPENSE),
    ("Checking", Decimal("42"), date(2026, 2, 19), "Dining Out", PostingType.EXPENSE),
    ("Travel Fund", Decimal("200"), date(2026, 2, 3), "Transport", PostingType.EXPENSE),
    ("Travel Fund", Decimal("150"), date(2026, 2, 10), "Dining Out", PostingType.EXPENSE),
    ("Travel Fund", Decimal("80"), date(2026, 2, 14), "Entertainment", PostingType.EXPENSE),
    ("Savings", Decimal("500"), date(2026, 2, 8), "Utilities", PostingType.EXPENSE),
    ("Cash", Decimal("1200"), date(2026, 2, 4), "Groceries", PostingType.EXPENSE),
]

# (source_name, dest_name, debit_amount, credit_amount, date, description)
TRANSFERS = [
    ("Checking", "Savings", Decimal("500"), Decimal("460"), date(2026, 1, 15), "USD → EUR savings"),
    (
        "Checking",
        "Cash",
        Decimal("300"),
        Decimal("27000"),
        date(2026, 1, 30),
        "USD → RUB cash top-up",
    ),
    (
        "Travel Fund",
        "Checking",
        Decimal("200"),
        Decimal("255"),
        date(2026, 2, 20),
        "GBP → USD rebalance",
    ),
]

TABLE_NAMES = ["transfer", "posting", "category", "account"]


def main() -> None:
    db = Database()
    db.init()
    session = db.get_session()

    try:
        # Truncate in FK-safe order
        for table in TABLE_NAMES:
            session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        session.commit()
        print("Truncated all tables.")

        # Create accounts
        accounts: dict[str, Account] = {}
        for name, currency, balance in ACCOUNTS:
            acc = Account(None, name, currency, balance)
            accounts[name] = acc
            session.add(acc)

        # Create categories
        categories: dict[str, Category] = {}
        for name in CATEGORIES:
            cat = Category(None, name)
            categories[name] = cat
            session.add(cat)

        # Flush so IDs are available for FKs
        session.flush()

        # Create postings via domain method
        for acc_name, amount, posting_date, cat_name, posting_type in POSTINGS:
            account = accounts[acc_name]
            account.record_posting(
                amount,
                posting_date,
                category_id=categories[cat_name].category_id,
                posting_type=posting_type,
            )

        # Create transfers via aggregate root methods
        for src, dst, debit, credit, t_date, desc in TRANSFERS:
            transfer = Transfer(
                transfer_id=None,
                source_account_id=accounts[src].account_id,
                dest_account_id=accounts[dst].account_id,
                debit_amount=debit,
                credit_amount=credit,
                transfer_date=t_date,
                description=desc,
            )
            accounts[src].record_outgoing_transfer(transfer)
            accounts[dst].record_incoming_transfer(transfer)
            session.add(transfer)

        session.commit()

        # Summary
        print(f"Seeded {len(accounts)} accounts:")
        for acc in accounts.values():
            print(f"  {acc.name} ({acc.currency}): balance {acc.balance}")
        print(f"Seeded {len(categories)} categories.")
        print(f"Seeded {len(POSTINGS)} postings.")
        print(f"Seeded {len(TRANSFERS)} transfers.")
        print("Done.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        db.dispose()


if __name__ == "__main__":
    main()
