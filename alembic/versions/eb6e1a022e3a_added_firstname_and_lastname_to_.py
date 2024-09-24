"""added firstname and lastname to attendees

Revision ID: eb6e1a022e3a
Revises: 1db093b780f6
Create Date: 2024-09-23 13:11:38.245777

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "eb6e1a022e3a"
down_revision: Union[str, None] = "1db093b780f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attendees", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("attendees", sa.Column("last_name", sa.String(), nullable=True))
    op.alter_column("attendees", "user_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.drop_column("attendees", "last_name")
    op.drop_column("attendees", "first_name")
    op.alter_column("attendees", "user_id", existing_type=sa.UUID(), nullable=False)
