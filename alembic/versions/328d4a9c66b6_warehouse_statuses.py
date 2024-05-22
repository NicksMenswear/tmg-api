"""warehouse-statuses

Revision ID: 328d4a9c66b6
Revises: 857d41b63f36
Create Date: 2024-05-22 20:59:39.549058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "328d4a9c66b6"
down_revision: Union[str, None] = "857d41b63f36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(f"ALTER TYPE rmastatus ADD VALUE 'WAREHOUSE_CANCELED';")


def downgrade() -> None:
    pass
