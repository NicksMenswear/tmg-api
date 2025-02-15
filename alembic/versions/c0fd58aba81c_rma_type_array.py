"""RMA type Array

Revision ID: c0fd58aba81c
Revises: 104060d3bee0
Create Date: 2024-03-18 20:43:09.713419

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c0fd58aba81c"
down_revision: Union[str, None] = "104060d3bee0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rmas",
        sa.Column(
            "type", sa.ARRAY(sa.Enum("RESIZE", "DAMAGED", "CANCELLATION", "EXCHANGE", name="rmatype")), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("rmas", "type")
