"""Add RMA

Revision ID: 9283fa414acd
Revises: c0fbaea979f1
Create Date: 2024-03-15 19:21:28.415635

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9283fa414acd"
down_revision: Union[str, None] = "c0fbaea979f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Removing legacy rma status enum
    with op.get_context().autocommit_block():
        op.execute("DROP TYPE IF EXISTS rmastatus;")

    rmastatus = sa.Enum("PENDING", "RECEIVED", "RESTOCKED", "CLOSED", name="rmastatus")

    rmatype = sa.Enum("RESIZE", "DAMAGED", "CANCELLATION", "EXCHANGE", name="rmatype")

    rmaitemtype = sa.Enum("DISLIKED", "TOO_BIG", "TOO_SMALL", "DAMAGED", "WRONG_ITEM", name="rmaitemtype")

    op.create_table(
        "rmas",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("rma_date", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("rma_number", sa.String(), nullable=True),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("total_items_expected", sa.Integer(), nullable=True),
        sa.Column("total_items_received", sa.Integer(), nullable=True),
        sa.Column("label_type", sa.String(), nullable=True),
        sa.Column("return_tracking", sa.String(), nullable=True),
        sa.Column("internal_return_note", sa.String(), nullable=True),
        sa.Column("customer_return_types", sa.String(), nullable=True),
        sa.Column("status", rmastatus, nullable=False),
        sa.Column("type", rmatype, nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("is_returned", sa.Boolean(), nullable=True),
        sa.Column("is_refunded", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )

    op.create_table(
        "rma_items",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("rma_id", sa.UUID(), nullable=True),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("purchased_price", sa.Numeric(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("type", rmaitemtype, nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rma_id"],
            ["rmas.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("rma_items")
    op.drop_table("rmas")
    op.execute("DROP TYPE rmastatus;")
    op.execute("DROP TYPE rmatype;")
    op.execute("DROP TYPE rmaitemtype;")
