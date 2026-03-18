from sqlalchemy import Table, Column, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy import Boolean, String, Numeric, Date, text
from sqlalchemy.orm import registry, relationship, backref

from app.domain import model

mapper_registry = registry()
metadata = mapper_registry.metadata

accounts = Table(
    "account",
    metadata,
    Column("account_id", String(36), primary_key=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("currency", String(3), nullable=False),
    Column("initial_balance", Numeric(precision=15, scale=2), nullable=False),
    Column("is_savings", Boolean, nullable=False, server_default="false"),
    Column("description", String(500), nullable=True),
)

categories = Table(
    "category",
    metadata,
    Column("category_id", String(36), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("parent_id", String(36), ForeignKey("category.category_id"), nullable=True),
    Column("category_type", String(20), nullable=False),
    Column("description", String(500), nullable=True),
    UniqueConstraint("parent_id", "name", name="uq_category_parent_name"),
)

Index(
    "uq_category_root_name",
    categories.c.name,
    unique=True,
    postgresql_where=categories.c.parent_id.is_(None),
)

postings = Table(
    "posting",
    metadata,
    Column("posting_id", String(36), primary_key=True),
    Column("account_id", String(36), ForeignKey("account.account_id"), nullable=False),
    Column("amount", Numeric(precision=15, scale=2), nullable=False),
    Column("posting_date", Date, nullable=False),
    Column("category_id", String(36), ForeignKey("category.category_id"), nullable=True),
    Column("posting_type", String(20), nullable=False),
    Column("payee", String(255), nullable=True),
    Column("description", String(500), nullable=True),
)

Index("ix_posting_payee_lower", func.lower(postings.c.payee))

transfers = Table(
    "transfer",
    metadata,
    Column("transfer_id", String(36), primary_key=True),
    Column("source_account_id", String(36), ForeignKey("account.account_id"), nullable=False),
    Column("dest_account_id", String(36), ForeignKey("account.account_id"), nullable=False),
    Column("debit_amount", Numeric(precision=15, scale=2), nullable=False),
    Column("credit_amount", Numeric(precision=15, scale=2), nullable=False),
    Column("transfer_date", Date, nullable=False),
    Column("description", String(500), nullable=True),
)


settings = Table(
    "settings",
    metadata,
    Column("settings_id", String(36), primary_key=True),
    Column("primary_currency", String(3), nullable=False, server_default=text("'EUR'")),
)


def start_mappers():
    mapper_registry.map_imperatively(
        model.Account,
        accounts,
        properties={
            "_postings": relationship(
                model.Posting,
                backref="account",
                cascade="save-update, merge, delete, delete-orphan",
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
    mapper_registry.map_imperatively(
        model.Category,
        categories,
        properties={
            "children": relationship(
                model.Category,
                backref=backref("parent", remote_side=[categories.c.category_id]),
                cascade="save-update, merge",
            ),
        },
    )
    mapper_registry.map_imperatively(model.Posting, postings)
    mapper_registry.map_imperatively(model.Transfer, transfers)
    mapper_registry.map_imperatively(
        model.Settings,
        settings,
        properties={
            "_primary_currency": settings.c.primary_currency,
        },
    )
