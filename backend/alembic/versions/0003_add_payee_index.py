"""add payee index

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-18 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX ix_posting_payee_lower ON posting (lower(payee) text_pattern_ops)")


def downgrade() -> None:
    op.drop_index("ix_posting_payee_lower", table_name="posting")
