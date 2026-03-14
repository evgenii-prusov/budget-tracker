"""add OAuth 2.1 tables for MCP server authentication

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-14 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
        sa.Column("scopes", sa.Text, nullable=False),  # space-separated
        sa.Column("code_challenge", sa.String, nullable=False),
        sa.Column("expires_at", sa.Float, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )

    op.create_table(
        "oauth_access_token",
        sa.Column("token", sa.String, primary_key=True),
        sa.Column("client_id", sa.String, nullable=False),
        sa.Column("scopes", sa.Text, nullable=False),  # space-separated
        sa.Column("expires_at", sa.Integer, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )

    op.create_table(
        "oauth_refresh_token",
        sa.Column("token", sa.String, primary_key=True),
        sa.Column("client_id", sa.String, nullable=False),
        sa.Column("scopes", sa.Text, nullable=False),  # space-separated
        sa.Column("expires_at", sa.Integer, nullable=True),
        sa.Column("access_token", sa.String, nullable=False),
        sa.Column("created_at", sa.Float, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oauth_refresh_token")
    op.drop_table("oauth_access_token")
    op.drop_table("oauth_authorization_code")
    op.drop_table("oauth_client")
