"""dropped variant_id and product_id and added price_compare_at columns for suit_builder_items

Revision ID: f3b7891d0811
Revises: 481f11a2f6ab
Create Date: 2024-11-06 08:29:12.227275

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3b7891d0811"
down_revision: Union[str, None] = "481f11a2f6ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("suit_builder_items", sa.Column("price_compare_at", sa.Numeric(), nullable=True))
    op.drop_column("suit_builder_items", "product_id")
    op.drop_column("suit_builder_items", "variant_id")


def downgrade() -> None:
    op.add_column("suit_builder_items", sa.Column("variant_id", sa.BIGINT(), autoincrement=False, nullable=True))
    op.add_column("suit_builder_items", sa.Column("product_id", sa.BIGINT(), autoincrement=False, nullable=True))
    op.drop_column("suit_builder_items", "price_compare_at")
