"""Added events table

Revision ID: f9f4a6a1d958
Revises: 94135d5b02ad
Create Date: 2024-04-25 21:07:10.737797

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9f4a6a1d958"
down_revision: Union[str, None] = "94135d5b02ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "events",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("event_name", sa.String(), nullable=False),
        sa.Column("event_date", sa.DateTime(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_events_is_active"), "events", ["is_active"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_events_is_active"), table_name="events")
    op.drop_table("events")
    # ### end Alembic commands ###
