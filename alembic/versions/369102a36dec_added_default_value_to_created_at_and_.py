"""added default value to created_at and updated_at fields

Revision ID: 369102a36dec
Revises: cc971d1e30cc
Create Date: 2024-08-02 11:18:20.763754

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "369102a36dec"
down_revision: Union[str, None] = "cc971d1e30cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE addresses ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE addresses ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE attendees ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE attendees ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE discounts ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE discounts ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE events ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE events ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE looks ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE looks ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE measurements ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE measurements ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE order_items ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE order_items ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE orders ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE orders ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE products ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE products ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE roles ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE roles ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE sizes ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE sizes ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE users ALTER COLUMN created_at SET DEFAULT now()")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT now()")
    op.execute("ALTER TABLE users ALTER COLUMN account_status SET DEFAULT FALSE")
    op.execute("ALTER TABLE webhooks ALTER COLUMN created_at SET DEFAULT now()")


def downgrade() -> None:
    pass
