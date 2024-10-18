"""user activity log

Revision ID: 01ebc7f29ca9
Revises: f8f16615eee9
Create Date: 2024-10-18 20:38:17.359318

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

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
    op.create_foreign_key(None, "attendees", "roles", ["role_id"], ["id"])
    op.create_foreign_key(None, "attendees", "users", ["user_id"], ["id"])
    op.create_index(op.f("ix_looks_name"), "looks", ["name"], unique=False)
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=False)
    op.alter_column(
        "users",
        "meta",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=True,
        existing_server_default=sa.text("'{}'::jsonb"),
    )
    op.drop_index("unique_lower_email", table_name="users")


def downgrade() -> None:
    op.create_index("unique_lower_email", "users", [sa.text("lower(email::text)")], unique=True)
    op.alter_column(
        "users",
        "meta",
        existing_type=postgresql.JSON(astext_type=sa.Text()),
        nullable=False,
        existing_server_default=sa.text("'{}'::jsonb"),
    )
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_index(op.f("ix_looks_name"), table_name="looks")
    op.drop_constraint(None, "attendees", type_="foreignkey")
    op.drop_constraint(None, "attendees", type_="foreignkey")
    op.drop_index(op.f("ix_user_activity_logs_user_id"), table_name="user_activity_logs")
    op.drop_table("user_activity_logs")
