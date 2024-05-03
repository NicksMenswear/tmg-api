"""Add order type

Revision ID: 34af4bdd0a19
Revises: 7bb2d4dee7fb
Create Date: 2024-03-10 13:35:15.170340

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "34af4bdd0a19"
down_revision: Union[str, None] = "7bb2d4dee7fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ordertype = sa.Enum(
        "NEW_ORDER",
        "FIRST_SUIT",
        "RESIZE",
        "GROOM_RESIZE",
        "SINGLE_SUIT",
        "SWATCH",
        "LOST",
        "DAMAGED",
        "MISSED_ORDER",
        "MISSED_ITEM",
        "ADDRESS_ERROR",
        "ADD_ON_ITEM",
        name="ordertype",
    )
    ordertype.create(op.get_bind())
    op.add_column("orders", sa.Column("order_type", sa.ARRAY(ordertype)))


def downgrade() -> None:
    op.drop_column("orders", "order_type")
    op.execute("DROP TYPE ordertype;")
