"""removed legacy fields from looks table

Revision ID: 03b149d9688c
Revises: 6d018c80dcb6
Create Date: 2024-05-02 15:25:33.650238

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "03b149d9688c"
down_revision: Union[str, None] = "6d018c80dcb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("looks_event_id_fkey", "looks", type_="foreignkey")
    op.drop_column("looks", "product_final_image")
    op.drop_column("looks", "event_id")


def downgrade() -> None:
    op.add_column("looks", sa.Column("event_id", sa.UUID(), autoincrement=False, nullable=True))
    op.add_column("looks", sa.Column("product_final_image", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_foreign_key("looks_event_id_fkey", "looks", "events", ["event_id"], ["id"])
