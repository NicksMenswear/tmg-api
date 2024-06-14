"""added image_path to looks table

Revision ID: 1477b09ba621
Revises: bdfc899663d7
Create Date: 2024-06-14 12:18:13.237005

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1477b09ba621"
down_revision: Union[str, None] = "bdfc899663d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("looks", sa.Column("image_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("looks", "image_path")
