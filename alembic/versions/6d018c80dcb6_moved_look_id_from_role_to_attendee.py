"""moved look_id from role to attendee

Revision ID: 6d018c80dcb6
Revises: 1165f59dc4f7
Create Date: 2024-05-01 16:50:51.238603

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6d018c80dcb6"
down_revision: Union[str, None] = "1165f59dc4f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attendees", sa.Column("look_id", sa.UUID(), nullable=True))
    op.create_foreign_key(None, "attendees", "looks", ["look_id"], ["id"])
    op.drop_constraint("rmas_id_key", "rmas", type_="unique")
    op.drop_constraint("roles_look_id_fkey", "roles", type_="foreignkey")
    op.drop_column("roles", "look_id")


def downgrade() -> None:
    op.add_column("roles", sa.Column("look_id", sa.UUID(), autoincrement=False, nullable=False))
    op.create_foreign_key("roles_look_id_fkey", "roles", "looks", ["look_id"], ["id"])
    op.drop_constraint(None, "attendees", type_="foreignkey")
    op.drop_column("attendees", "look_id")
