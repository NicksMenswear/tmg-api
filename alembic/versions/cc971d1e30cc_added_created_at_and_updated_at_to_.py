"""added created_at and updated_at to addresses table

Revision ID: cc971d1e30cc
Revises: 8ba155b1e6da
Create Date: 2024-08-02 09:41:27.261890

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc971d1e30cc"
down_revision: Union[str, None] = "8ba155b1e6da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("addresses", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("addresses", sa.Column("updated_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE addresses SET created_at = now(), updated_at = now()")

    op.alter_column("addresses", "created_at", nullable=False)
    op.alter_column("addresses", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("addresses", "updated_at")
    op.drop_column("addresses", "created_at")
