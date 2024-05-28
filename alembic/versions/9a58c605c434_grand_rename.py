"""grand_rename

Revision ID: 9a58c605c434
Revises: 328d4a9c66b6
Create Date: 2024-05-28 14:12:52.506376

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a58c605c434"
down_revision: Union[str, None] = "328d4a9c66b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create columns
    op.add_column("events", sa.Column("name", sa.String(), nullable=True))
    op.add_column("looks", sa.Column("name", sa.String(), nullable=True))
    op.add_column("roles", sa.Column("name", sa.String(), nullable=True))

    # copy data
    op.execute("UPDATE events SET name = event_name")
    op.execute("UPDATE looks SET name = look_name")
    op.execute("UPDATE roles SET name = role_name")

    # alter columns
    op.alter_column("events", "name", nullable=False)
    op.alter_column("looks", "name", nullable=False)
    op.alter_column("roles", "name", nullable=False)

    # drop columns
    op.drop_column("events", "event_name")
    op.drop_column("looks", "look_name")
    op.drop_column("roles", "role_name")


def downgrade() -> None:
    # add columns
    op.add_column("events", sa.Column("event_name", sa.VARCHAR(), nullable=True))
    op.add_column("looks", sa.Column("look_name", sa.VARCHAR(), nullable=True))
    op.add_column("roles", sa.Column("role_name", sa.VARCHAR(), nullable=True))

    # copy data
    op.execute("UPDATE events SET event_name = name")
    op.execute("UPDATE looks SET look_name = name")
    op.execute("UPDATE roles SET role_name = name")

    # alter columns
    op.alter_column("events", "event_name", nullable=False)
    op.alter_column("looks", "look_name", nullable=False)
    op.alter_column("roles", "role_name", nullable=False)

    # drop columns
    op.drop_column("events", "name")
    op.drop_column("looks", "name")
    op.drop_column("roles", "name")
