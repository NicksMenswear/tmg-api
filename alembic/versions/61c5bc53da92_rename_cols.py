"""rename cols

Revision ID: 61c5bc53da92
Revises: 4ed280b49c44
Create Date: 2024-05-07 20:28:56.341998

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "61c5bc53da92"
down_revision: Union[str, None] = "4ed280b49c44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    rmaitemtype = postgresql.ENUM("REFUND", "EXCHANGE", name="rmaitemtype")
    rmaitemtype.create(op.get_bind())
    rmastatus = postgresql.ENUM("PENDING", "PENDING_CS_ACTION", "WAREHOUSE_COMPLETE", "COMPLETED", name="rmastatus")
    rmastatus.create(op.get_bind())

    op.alter_column(
        "rma_items",
        "type",
        existing_type=postgresql.ENUM("REFUND", "EXCHANGE", name="rmaitemtype2"),
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using="type::VARCHAR",
    )
    op.alter_column(
        "rmas",
        "status",
        existing_type=postgresql.ENUM(
            "PENDING", "PENDING_CS_ACTION", "WAREHOUSE_COMPLETE", "COMPLETED", name="rmastatus2"
        ),
        type_=sa.String(),
        existing_nullable=False,
        postgresql_using="type::VARCHAR",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    pass
