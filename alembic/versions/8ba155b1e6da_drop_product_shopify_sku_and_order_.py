"""drop product.shopify_sku and order_items.price columns

Revision ID: 8ba155b1e6da
Revises: 45446d04cc33
Create Date: 2024-07-24 12:35:17.894414

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8ba155b1e6da"
down_revision: Union[str, None] = "45446d04cc33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("order_items", "price")
    op.drop_column("products", "shopify_sku")


def downgrade() -> None:
    op.add_column("products", sa.Column("shopify_sku", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column(
        "order_items", sa.Column("price", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
