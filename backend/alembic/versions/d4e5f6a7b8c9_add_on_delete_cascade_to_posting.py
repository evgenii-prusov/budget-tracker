"""add ON DELETE CASCADE to posting.account_id foreign key

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-14 00:00:00.000000

"""

from typing import Sequence, Union


from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing FK constraint (no cascade)
    op.drop_constraint("posting_account_id_fkey", "posting", type_="foreignkey")
    # Recreate with ON DELETE CASCADE
    op.create_foreign_key(
        "posting_account_id_fkey",
        "posting",
        "account",
        ["account_id"],
        ["account_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("posting_account_id_fkey", "posting", type_="foreignkey")
    op.create_foreign_key(
        "posting_account_id_fkey",
        "posting",
        "account",
        ["account_id"],
        ["account_id"],
    )
