"""user activity log

Revision ID: 01ebc7f29ca9
Revises: f8f16615eee9
Create Date: 2024-10-18 20:38:17.359318

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "01ebc7f29ca9"
down_revision: Union[str, None] = "f8f16615eee9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_activity_logs",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("audit_log_id", sa.UUID(), nullable=False),
        sa.Column("handle", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["audit_log_id"],
            ["audit_logs.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_activity_logs_user_id"), "user_activity_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_activity_logs_user_id"), table_name="user_activity_logs")
    op.drop_table("user_activity_logs")
