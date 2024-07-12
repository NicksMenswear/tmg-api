"""drop product_items table

Revision ID: 5917dbdc0b50
Revises: cc0bb2680c65
Create Date: 2024-07-12 11:54:10.092392

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5917dbdc0b50"
down_revision: Union[str, None] = "cc0bb2680c65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_product_items_is_active", table_name="product_items")
    op.drop_table("product_items")


def downgrade() -> None:
    op.create_table(
        "product_items",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), autoincrement=False, nullable=False),
        sa.Column("is_active", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("sku", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("weight_lb", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column("height_in", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column("width_in", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column("length_in", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column("value", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column("price", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column("on_hand", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("allocated", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("reserve", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("non_sellable_total", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("reorder_level", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("reorder_amount", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("replenishment_level", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("available", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("backorder", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("barcode", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="product_items_pkey"),
    )
    op.create_index("ix_product_items_is_active", "product_items", ["is_active"], unique=False)
