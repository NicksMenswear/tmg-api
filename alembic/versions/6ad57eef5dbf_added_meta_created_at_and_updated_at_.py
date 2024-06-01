"""added meta, created_at and updated_at fields for order, order_item and product models

Revision ID: 6ad57eef5dbf
Revises: 206dc1277a03
Create Date: 2024-05-31 17:57:13.616163

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6ad57eef5dbf"
down_revision: Union[str, None] = "206dc1277a03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # add columns
    op.add_column("orders", sa.Column("meta", sa.JSON(), nullable=True))
    op.add_column("orders", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("orders", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("products", sa.Column("meta", sa.JSON(), nullable=True))
    op.add_column("products", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("products", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("order_items", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("order_items", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # set default values
    op.execute("UPDATE orders SET created_at = now(), updated_at = now(), meta = '{}'")
    op.execute("UPDATE products SET created_at = now(), updated_at = now(), meta = '{}'")
    op.execute("UPDATE order_items SET created_at = now(), updated_at = now()")

    # set not null
    op.alter_column("orders", "created_at", nullable=False)
    op.alter_column("orders", "updated_at", nullable=False)
    op.alter_column("orders", "meta", nullable=False)
    op.alter_column("products", "created_at", nullable=False)
    op.alter_column("products", "updated_at", nullable=False)
    op.alter_column("products", "meta", nullable=False)
    op.alter_column("order_items", "created_at", nullable=False)
    op.alter_column("order_items", "updated_at", nullable=False)


def downgrade() -> None:
    op.drop_column("products", "meta")
    op.drop_column("products", "created_at")
    op.drop_column("products", "updated_at")
    op.drop_column("orders", "meta")
    op.drop_column("orders", "created_at")
    op.drop_column("orders", "updated_at")
    op.drop_column("order_items", "created_at")
    op.drop_column("order_items", "updated_at")
