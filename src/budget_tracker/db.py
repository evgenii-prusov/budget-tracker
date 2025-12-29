from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import String, Numeric, Date
from sqlalchemy.orm import registry, relationship

from budget_tracker import model

mapper_registry = registry()
metadata = mapper_registry.metadata

accounts = Table(
    "account",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("currency", String, nullable=False),
    Column("initial_balance", Numeric, nullable=False),
)

entries = Table(
    "entry",
    metadata,
    Column("id", String, primary_key=True),
    Column("account_id", String, ForeignKey("account.id"), nullable=False),
    Column("amount", Numeric, nullable=False),
    Column("entry_date", Date, nullable=False),
    Column("category", String, nullable=False),
    Column("category_type", String, nullable=False),
)


def start_mappers():
    mapper_registry.map_imperatively(
        model.Account,
        accounts,
        properties={
            "_entries": relationship(
                model.Entry,
                backref="account",
                cascade="all, delete-orphan",
            ),
        },
    )
    mapper_registry.map_imperatively(model.Entry, entries)
