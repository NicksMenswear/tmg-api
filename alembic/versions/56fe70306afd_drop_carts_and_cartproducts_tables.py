"""drop carts and cartproducts tables

Revision ID: 56fe70306afd
Revises: ea0e8b05dac5
Create Date: 2024-05-30 16:41:10.715255

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "56fe70306afd"
down_revision: Union[str, None] = "ea0e8b05dac5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("cartproducts")
    op.drop_table("carts")


def downgrade() -> None:
    op.create_table(
        "carts",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("attendee_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["attendee_id"],
            ["attendees.id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cartproducts",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("cart_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=True),
        sa.Column("variation_id", sa.BigInteger(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["carts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
