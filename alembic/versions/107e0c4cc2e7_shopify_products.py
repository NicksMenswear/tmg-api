"""shopify products

Revision ID: 107e0c4cc2e7
Revises: f3b7891d0811
Create Date: 2024-11-07 17:52:33.141613

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "107e0c4cc2e7"
down_revision: Union[str, None] = "f3b7891d0811"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shopify_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("product_id", sa.BigInteger(), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )

    op.create_index(op.f("ix_shopify_products_product_id"), "shopify_products", ["product_id"], unique=True)

    # Create a GIN index on the `variants.id` field in the JSONB `data` column
    op.execute(
        """
        CREATE INDEX ix_shopify_products_variants_id
        ON shopify_products
        USING GIN ((jsonb_path_query_array(data, '$.variants[*].id')) jsonb_path_ops);
    """
    )

    # Create a GIN index on the `variants.sku` field in the JSONB `data` column
    op.execute(
        """
        CREATE INDEX ix_shopify_products_variants_sku
        ON shopify_products
        USING GIN ((jsonb_path_query_array(data, '$.variants[*].sku')) jsonb_path_ops);
    """
    )


def downgrade() -> None:
    op.drop_index("ix_shopify_products_variants_id", table_name="shopify_products")
    op.drop_index("ix_shopify_products_variants_sku", table_name="shopify_products")
    op.drop_index(op.f("ix_shopify_products_product_id"), table_name="shopify_products")
    op.drop_table("shopify_products")
