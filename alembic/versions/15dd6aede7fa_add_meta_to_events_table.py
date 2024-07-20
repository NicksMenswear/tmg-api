"""add meta to events table

Revision ID: 15dd6aede7fa
Revises: d8763990bec6
Create Date: 2024-07-20 11:41:23.308088

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15dd6aede7fa"
down_revision: Union[str, None] = "d8763990bec6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("events", sa.Column("meta", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "meta")
