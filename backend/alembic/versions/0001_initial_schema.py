"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-15 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "account",
        sa.Column("account_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("initial_balance", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("is_savings", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("description", sa.String(500), nullable=True),
    )

    op.create_table(
        "category",
        sa.Column("category_id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("category.category_id"), nullable=True),
        sa.Column("category_type", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.UniqueConstraint("parent_id", "name", name="uq_category_parent_name"),
    )

    op.create_index(
        "uq_category_root_name",
        "category",
        ["name"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )

    op.create_table(
        "posting",
        sa.Column("posting_id", sa.String(36), primary_key=True),
        sa.Column(
            "account_id",
            sa.String(36),
            sa.ForeignKey("account.account_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("posting_date", sa.Date, nullable=False),
        sa.Column(
            "category_id", sa.String(36), sa.ForeignKey("category.category_id"), nullable=True
        ),
        sa.Column("posting_type", sa.String(20), nullable=False),
        sa.Column("payee", sa.String(255), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
    )

    op.create_table(
        "transfer",
        sa.Column("transfer_id", sa.String(36), primary_key=True),
        sa.Column(
            "source_account_id",
            sa.String(36),
            sa.ForeignKey("account.account_id"),
            nullable=False,
        ),
        sa.Column(
            "dest_account_id",
            sa.String(36),
            sa.ForeignKey("account.account_id"),
            nullable=False,
        ),
        sa.Column("debit_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("credit_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("transfer_date", sa.Date, nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
    )

    op.create_table(
        "oauth_client",
        sa.Column("client_id", sa.String, primary_key=True),
        sa.Column("client_info_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )

    op.create_table(
        "oauth_authorization_code",
        sa.Column("code", sa.String, primary_key=True),
        sa.Column("client_id", sa.String, nullable=False),
        sa.Column("redirect_uri", sa.Text, nullable=False),
        sa.Column("redirect_uri_provided_explicitly", sa.Boolean, nullable=False),
        sa.Column("scopes", sa.Text, nullable=False),
        sa.Column("code_challenge", sa.String, nullable=False),
        sa.Column("expires_at", sa.Float, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )

    op.create_table(
        "oauth_access_token",
        sa.Column("token", sa.String, primary_key=True),
        sa.Column("client_id", sa.String, nullable=False),
        sa.Column("scopes", sa.Text, nullable=False),
        sa.Column("expires_at", sa.Integer, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )

    op.create_table(
        "oauth_refresh_token",
        sa.Column("token", sa.String, primary_key=True),
        sa.Column("client_id", sa.String, nullable=False),
        sa.Column("scopes", sa.Text, nullable=False),
        sa.Column("expires_at", sa.Integer, nullable=True),
        sa.Column("access_token", sa.String, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oauth_refresh_token")
    op.drop_table("oauth_access_token")
    op.drop_table("oauth_authorization_code")
    op.drop_table("oauth_client")
    op.drop_table("transfer")
    op.drop_table("posting")
    op.drop_table("category")
    op.drop_table("account")
