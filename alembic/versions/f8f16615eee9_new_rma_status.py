"""new RMA status

Revision ID: f8f16615eee9
Revises: 59d0bb205ba5
Create Date: 2024-10-18 19:26:44.066108

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f8f16615eee9"
down_revision: Union[str, None] = "59d0bb205ba5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE rmastatus ADD VALUE 'CS_COMPLETE';")


def downgrade() -> None:
    pass
