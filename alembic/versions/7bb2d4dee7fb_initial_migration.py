"""Initial migration

Revision ID: 7bb2d4dee7fb
Revises: 
Create Date: 2024-03-05 19:28:12.756740

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7bb2d4dee7fb"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, "addresses", ["id"])
    op.create_unique_constraint(None, "order_items", ["id"])
    op.create_unique_constraint(None, "orders", ["id"])
    op.create_unique_constraint(None, "products", ["id"])
    op.create_unique_constraint(None, "users", ["id"])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "users", type_="unique")
    op.drop_constraint(None, "products", type_="unique")
    op.drop_constraint(None, "orders", type_="unique")
    op.drop_constraint(None, "order_items", type_="unique")
    op.drop_constraint(None, "addresses", type_="unique")
    # ### end Alembic commands ###
