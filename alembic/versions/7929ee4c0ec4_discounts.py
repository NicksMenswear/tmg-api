"""discounts

Revision ID: 7929ee4c0ec4
Revises: f7a376258cb7
Create Date: 2024-05-17 12:47:48.324823

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7929ee4c0ec4"
down_revision: Union[str, None] = "f7a376258cb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discounts",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("attendee_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column(
            "type", sa.Enum("GROOM_GIFT", "GROOM_FULL_PAY", "PARTY_OF_FOUR", name="discounttype"), nullable=False
        ),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("shopify_discount_code_id", sa.String(), nullable=True),
        sa.Column("shopify_virtual_product_id", sa.String(), nullable=True),
        sa.Column("shopify_virtual_product_variant_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["attendee_id"],
            ["attendees.id"],
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("discounts")
    op.execute("DROP TYPE IF EXISTS discounttype")
