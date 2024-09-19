"""added suit builder

Revision ID: 85876b6d2125
Revises: 866573db5e09
Create Date: 2024-09-19 15:15:05.066605

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "85876b6d2125"
down_revision: Union[str, None] = "866573db5e09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suit_builder_items",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "SUIT",
                "SHIRT",
                "NECK_TIE",
                "BOW_TIE",
                "PREMIUM_POCKET_SQUARE",
                "SHOES",
                "BELT",
                "SOCKS",
                name="suitbuilderitemtype",
            ),
            nullable=False,
        ),
        sa.Column("sku", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("index", sa.Integer(), nullable=False),
        sa.Column("variant_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("price", sa.Numeric(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )


def downgrade() -> None:
    op.drop_table("suit_builder_items")
