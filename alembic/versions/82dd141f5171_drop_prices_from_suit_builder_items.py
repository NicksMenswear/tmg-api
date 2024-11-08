"""drop prices from suit builder items

Revision ID: 82dd141f5171
Revises: 107e0c4cc2e7
Create Date: 2024-11-08 10:53:24.527555

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "82dd141f5171"
down_revision: Union[str, None] = "107e0c4cc2e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("suit_builder_items", "price_compare_at")
    op.drop_column("suit_builder_items", "price")


def downgrade() -> None:
    op.add_column("suit_builder_items", sa.Column("price", sa.NUMERIC(), autoincrement=False, nullable=False))
    op.add_column("suit_builder_items", sa.Column("price_compare_at", sa.NUMERIC(), autoincrement=False, nullable=True))
