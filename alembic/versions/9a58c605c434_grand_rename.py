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
    op.add_column("events", sa.Column("event_at", sa.DateTime(), nullable=True))
    op.add_column("looks", sa.Column("name", sa.String(), nullable=True))
    op.add_column("roles", sa.Column("name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("events", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("events", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("looks", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("looks", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("roles", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("roles", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("attendees", sa.Column("role_id", sa.UUID(), nullable=True))
    op.add_column("attendees", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("attendees", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # copy data and set defaults
    op.execute("UPDATE events SET name = event_name")
    op.execute("UPDATE events SET event_at = event_date")
    op.execute("UPDATE looks SET name = look_name")
    op.execute("UPDATE roles SET name = role_name")
    op.execute("UPDATE events SET created_at = now()")
    op.execute("UPDATE events SET updated_at = now()")
    op.execute("UPDATE looks SET created_at = now()")
    op.execute("UPDATE looks SET updated_at = now()")
    op.execute("UPDATE roles SET created_at = now()")
    op.execute("UPDATE roles SET updated_at = now()")
    op.execute("UPDATE users SET created_at = now()")
    op.execute("UPDATE users SET updated_at = now()")
    op.execute("UPDATE attendees SET role_id = role")
    op.execute("UPDATE attendees SET created_at = now()")
    op.execute("UPDATE attendees SET updated_at = now()")

    # alter columns
    op.alter_column("events", "name", nullable=False)
    op.alter_column("events", "event_at", nullable=False)
    op.alter_column("looks", "name", nullable=False)
    op.alter_column("roles", "name", nullable=False)
    op.alter_column("users", "created_at", nullable=False)
    op.alter_column("users", "updated_at", nullable=False)
    op.alter_column("events", "created_at", nullable=False)
    op.alter_column("events", "updated_at", nullable=False)
    op.alter_column("looks", "created_at", nullable=False)
    op.alter_column("looks", "updated_at", nullable=False)
    op.alter_column("roles", "created_at", nullable=False)
    op.alter_column("roles", "updated_at", nullable=False)
    op.alter_column("attendees", "created_at", nullable=False)
    op.alter_column("attendees", "updated_at", nullable=False)
    op.alter_column("discounts", "created_at", nullable=False)
    op.alter_column("discounts", "updated_at", nullable=False)

    # drop columns
    op.drop_column("events", "event_name")
    op.drop_column("events", "event_date")
    op.drop_column("looks", "look_name")
    op.drop_column("roles", "role_name")
    op.drop_column("attendees", "role")


def downgrade() -> None:
    # add columns
    op.add_column("events", sa.Column("event_name", sa.VARCHAR(), nullable=True))
    op.add_column("looks", sa.Column("look_name", sa.VARCHAR(), nullable=True))
    op.add_column("roles", sa.Column("role_name", sa.VARCHAR(), nullable=True))
    op.add_column("events", sa.Column("event_date", sa.VARCHAR(), nullable=True))
    op.add_column("attendees", sa.Column("role", sa.UUID(), nullable=True))

    # copy data
    op.execute("UPDATE events SET event_name = name")
    op.execute("UPDATE events SET event_date = event_at")
    op.execute("UPDATE looks SET look_name = name")
    op.execute("UPDATE roles SET role_name = name")
    op.execute("UPDATE attendees SET role = role_id")

    # alter columns
    op.alter_column("events", "event_name", nullable=False)
    op.alter_column("events", "event_at", nullable=False)
    op.alter_column("looks", "look_name", nullable=False)
    op.alter_column("roles", "role_name", nullable=False)

    # drop columns
    op.drop_column("events", "name")
    op.drop_column("events", "event_at")
    op.drop_column("looks", "name")
    op.drop_column("roles", "name")
    op.drop_column("users", "created_at")
    op.drop_column("users", "updated_at")
    op.drop_column("events", "created_at")
    op.drop_column("events", "updated_at")
    op.drop_column("looks", "created_at")
    op.drop_column("looks", "updated_at")
    op.drop_column("roles", "created_at")
    op.drop_column("roles", "updated_at")
    op.drop_column("attendees", "role_id")
    op.drop_column("attendees", "created_at")
    op.drop_column("attendees", "updated_at")
