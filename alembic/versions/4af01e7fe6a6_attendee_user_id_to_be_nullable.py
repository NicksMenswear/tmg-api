"""attendee user_id to be nullable

Revision ID: 4af01e7fe6a6
Revises: eb6e1a022e3a
Create Date: 2024-09-23 15:27:16.839403

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4af01e7fe6a6"
down_revision: Union[str, None] = "eb6e1a022e3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("attendees", "user_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column("attendees", "user_id", existing_type=sa.UUID(), nullable=False)
