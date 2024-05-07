"""rename types

Revision ID: f7a376258cb7
Revises: 61c5bc53da92
Create Date: 2024-05-07 20:51:05.192601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f7a376258cb7"
down_revision: Union[str, None] = "61c5bc53da92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    rmaitemtype = postgresql.ENUM("REFUND", "EXCHANGE", name="rmaitemtype")
    rmastatus = postgresql.ENUM("PENDING", "PENDING_CS_ACTION", "WAREHOUSE_COMPLETE", "COMPLETED", name="rmastatus")

    op.alter_column(
        "rma_items",
        "type",
        existing_type=sa.String(),
        type_=rmaitemtype,
        existing_nullable=False,
        postgresql_using="type::rmaitemtype",
    )
    op.alter_column(
        "rmas",
        "status",
        existing_type=sa.String(),
        type_=rmastatus,
        existing_nullable=False,
        postgresql_using="status::rmastatus",
    )


def downgrade() -> None:
    pass
