"""add shopify_order_number column

Revision ID: b1eca0d77d70
Revises: 3a3ae45cf1be
Create Date: 2024-07-04 19:37:40.795216

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1eca0d77d70"
down_revision: Union[str, None] = "3a3ae45cf1be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("shopify_order_number", sa.String(), nullable=True))
    op.create_unique_constraint(None, "orders", ["shopify_order_number"])


def downgrade() -> None:
    op.drop_constraint(None, "orders", type_="unique")
    op.drop_column("orders", "shopify_order_number")
