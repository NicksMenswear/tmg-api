"""change attendee progress column types to boolean

Revision ID: 7016ddb603c9
Revises: 56fe70306afd
Create Date: 2024-05-30 17:06:44.330111

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7016ddb603c9"
down_revision: Union[str, None] = "56fe70306afd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("attendees", "style")
    op.drop_column("attendees", "invite")
    op.drop_column("attendees", "pay")
    op.drop_column("attendees", "size")
    op.drop_column("attendees", "ship")

    op.add_column("attendees", sa.Column("style", sa.Boolean(), nullable=True))
    op.add_column("attendees", sa.Column("invite", sa.Boolean(), nullable=True))
    op.add_column("attendees", sa.Column("pay", sa.Boolean(), nullable=True))
    op.add_column("attendees", sa.Column("size", sa.Boolean(), nullable=True))
    op.add_column("attendees", sa.Column("ship", sa.Boolean(), nullable=True))

    op.execute("UPDATE attendees SET style = FALSE")
    op.execute("UPDATE attendees SET invite = FALSE")
    op.execute("UPDATE attendees SET pay = FALSE")
    op.execute("UPDATE attendees SET size = FALSE")
    op.execute("UPDATE attendees SET ship = FALSE")

    op.alter_column("attendees", "style", nullable=False)
    op.alter_column("attendees", "invite", nullable=False)
    op.alter_column("attendees", "pay", nullable=False)
    op.alter_column("attendees", "size", nullable=False)
    op.alter_column("attendees", "ship", nullable=False)


def downgrade() -> None:
    op.drop_column("attendees", "style")
    op.drop_column("attendees", "invite")
    op.drop_column("attendees", "pay")
    op.drop_column("attendees", "size")
    op.drop_column("attendees", "ship")

    op.add_column("attendees", sa.Column("style", sa.Integer(), nullable=True))
    op.add_column("attendees", sa.Column("invite", sa.Integer(), nullable=True))
    op.add_column("attendees", sa.Column("pay", sa.Integer(), nullable=True))
    op.add_column("attendees", sa.Column("size", sa.Integer(), nullable=True))
    op.add_column("attendees", sa.Column("ship", sa.Integer(), nullable=True))

    op.execute("UPDATE attendees SET style = 0")
    op.execute("UPDATE attendees SET invite = 0")
    op.execute("UPDATE attendees SET pay = 0")
    op.execute("UPDATE attendees SET size = 0")
    op.execute("UPDATE attendees SET ship = 0")

    op.alter_column("attendees", "style", nullable=False)
    op.alter_column("attendees", "invite", nullable=False)
    op.alter_column("attendees", "pay", nullable=False)
    op.alter_column("attendees", "size", nullable=False)
    op.alter_column("attendees", "ship", nullable=False)
