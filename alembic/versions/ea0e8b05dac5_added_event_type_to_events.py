"""added event type to events

Revision ID: ea0e8b05dac5
Revises: a1cd0e119c50
Create Date: 2024-05-30 11:27:23.197435

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ea0e8b05dac5"
down_revision: Union[str, None] = "a1cd0e119c50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create enum type
    event_type = sa.Enum("WEDDING", "PROM", "OTHER", name="eventtype")
    event_type.create(op.get_bind())

    # create column
    op.add_column("events", sa.Column("type", event_type, nullable=True))

    # set default value
    op.execute("UPDATE events SET type = 'WEDDING'")

    # set not null
    op.alter_column("events", "type", nullable=False)


def downgrade() -> None:
    # drop column
    op.drop_column("events", "type")

    # drop enum type
    op.execute("DROP TYPE eventtype")
