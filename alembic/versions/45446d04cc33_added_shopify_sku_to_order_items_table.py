"""added shopify_sku to order_items table

Revision ID: 45446d04cc33
Revises: 15dd6aede7fa
Create Date: 2024-07-23 18:20:10.296962

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "45446d04cc33"
down_revision: Union[str, None] = "15dd6aede7fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("order_items", sa.Column("shopify_sku", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("order_items", "shopify_sku")
