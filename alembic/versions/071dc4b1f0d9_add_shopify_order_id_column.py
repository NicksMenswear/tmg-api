"""add shopify_order_id column

Revision ID: 071dc4b1f0d9
Revises: b1eca0d77d70
Create Date: 2024-07-05 15:06:42.461939

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "071dc4b1f0d9"
down_revision: Union[str, None] = "b1eca0d77d70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("shopify_order_id", sa.String(), nullable=True))
    op.create_unique_constraint(None, "orders", ["shopify_order_id"])


def downgrade() -> None:
    op.drop_constraint(None, "orders", type_="unique")
    op.drop_column("orders", "shopify_order_id")
