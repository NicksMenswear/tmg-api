"""Add item_status

Revision ID: c0fbaea979f1
Revises: 34af4bdd0a19
Create Date: 2024-03-12 16:19:48.418558

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c0fbaea979f1"
down_revision: Union[str, None] = "34af4bdd0a19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    itemstatus = sa.Enum("ORDERED", "FULFILLED", "SHIPPED", "RETURNED", "REFUNDED", "BACKORDER", name="itemstatus")
    itemstatus.create(op.get_bind())
    op.add_column("order_items", sa.Column("item_status", itemstatus, nullable=True))


def downgrade() -> None:
    op.drop_column("order_items", "item_status")
    op.execute("DROP TYPE itemstatus;")
