from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import String, Numeric, Date
from sqlalchemy.orm import registry, relationship

from app.domain import model

mapper_registry = registry()
metadata = mapper_registry.metadata

accounts = Table(
    "account",
    metadata,
    Column("account_id", String, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("currency", String, nullable=False),
    Column("initial_balance", Numeric, nullable=False),
)

categories = Table(
    "category",
    metadata,
    Column("category_id", String, primary_key=True),
    Column("name", String, nullable=False, unique=True),
)

postings = Table(
    "posting",
    metadata,
    Column("posting_id", String, primary_key=True),
    Column("account_id", String, ForeignKey("account.account_id"), nullable=False),
    Column("amount", Numeric, nullable=False),
    Column("posting_date", Date, nullable=False),
    Column("category_id", String, ForeignKey("category.category_id"), nullable=True),
    Column("posting_type", String, nullable=False),
)

transfers = Table(
    "transfer",
    metadata,
    Column("transfer_id", String, primary_key=True),
    Column(
        "source_account_id", String, ForeignKey("account.account_id"), nullable=False
    ),
    Column("dest_account_id", String, ForeignKey("account.account_id"), nullable=False),
    Column("debit_amount", Numeric, nullable=False),
    Column("credit_amount", Numeric, nullable=False),
    Column("transfer_date", Date, nullable=False),
    Column("description", String, nullable=True),
)


def start_mappers():
    mapper_registry.map_imperatively(
        model.Account,
        accounts,
        properties={
            "_postings": relationship(
                model.Posting,
                backref="account",
                cascade="save-update, merge",
                passive_deletes=True,
            ),
            "_outgoing_transfers": relationship(
                model.Transfer,
                foreign_keys=[transfers.c.source_account_id],
                backref="source_account",
            ),
            "_incoming_transfers": relationship(
                model.Transfer,
                foreign_keys=[transfers.c.dest_account_id],
                backref="dest_account",
            ),
        },
    )
    mapper_registry.map_imperatively(model.Category, categories)
    mapper_registry.map_imperatively(model.Posting, postings)
    mapper_registry.map_imperatively(model.Transfer, transfers)
