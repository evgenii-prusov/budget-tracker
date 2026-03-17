"""add settings table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-17 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("settings_id", sa.String(36), primary_key=True),
        sa.Column(
            "primary_currency",
            sa.String(3),
            nullable=False,
            server_default="EUR",
        ),
    )


def downgrade() -> None:
    op.drop_table("settings")
