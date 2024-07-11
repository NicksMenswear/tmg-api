"""add shopify_sku column

Revision ID: cc0bb2680c65
Revises: 071dc4b1f0d9
Create Date: 2024-07-11 09:57:33.926472

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc0bb2680c65"
down_revision: Union[str, None] = "071dc4b1f0d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("shiphero_sku", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "shiphero_sku")
