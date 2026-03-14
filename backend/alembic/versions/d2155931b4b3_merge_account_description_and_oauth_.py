"""merge account description and oauth tables

Revision ID: d2155931b4b3
Revises: 04ef053e6041, e5f6a7b8c9d0
Create Date: 2026-03-15 00:00:47.781942

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "d2155931b4b3"
down_revision: Union[str, Sequence[str], None] = ("04ef053e6041", "e5f6a7b8c9d0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
