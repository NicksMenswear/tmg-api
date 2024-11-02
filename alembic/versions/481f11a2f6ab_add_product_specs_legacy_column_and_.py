"""add product_specs_legacy column and clone product_specs there

Revision ID: 481f11a2f6ab
Revises: 48360ab6ecae
Create Date: 2024-11-02 18:56:47.654752

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "481f11a2f6ab"
down_revision: Union[str, None] = "48360ab6ecae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("looks", sa.Column("product_specs_legacy", sa.JSON(), nullable=True))
    op.execute("UPDATE looks SET product_specs_legacy = product_specs")


def downgrade() -> None:
    op.drop_column("looks", "product_specs_legacy")
