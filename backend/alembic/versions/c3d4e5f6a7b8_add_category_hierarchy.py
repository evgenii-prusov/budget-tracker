"""add category hierarchy

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-08 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add category_type as nullable first for data migration
    op.add_column(
        "category",
        sa.Column("category_type", sa.String(20), nullable=True, server_default="EXPENSE"),
    )
    # Add parent_id self-referential FK
    op.add_column(
        "category",
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("category.category_id"), nullable=True),
    )

    # Backfill existing categories as EXPENSE parents
    op.execute("UPDATE category SET category_type = 'EXPENSE' WHERE category_type IS NULL")

    # Make category_type NOT NULL
    op.alter_column("category", "category_type", nullable=False)
    # Remove server_default now that the column is NOT NULL and all rows are populated
    op.alter_column("category", "category_type", server_default=None)

    # Drop old unique constraint on name and add composite unique
    op.drop_constraint("uq_category_name", "category", type_="unique")
    op.create_unique_constraint("uq_category_parent_name", "category", ["parent_id", "name"])
    # Partial index to enforce uniqueness among root categories (parent_id IS NULL)
    op.create_index(
        "uq_category_root_name",
        "category",
        ["name"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_category_root_name", table_name="category")
    op.drop_constraint("uq_category_parent_name", "category", type_="unique")
    op.create_unique_constraint("uq_category_name", "category", ["name"])
    op.drop_column("category", "parent_id")
    op.drop_column("category", "category_type")
