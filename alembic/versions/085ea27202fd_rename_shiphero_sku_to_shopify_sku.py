"""rename shiphero_sku to shopify_sku

Revision ID: 085ea27202fd
Revises: 5917dbdc0b50
Create Date: 2024-07-12 12:04:53.478041

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "085ea27202fd"
down_revision: Union[str, None] = "5917dbdc0b50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("shopify_sku", sa.String(), nullable=True))
    op.drop_column("products", "shiphero_sku")


def downgrade() -> None:
    op.add_column("products", sa.Column("shiphero_sku", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column("products", "shopify_sku")
