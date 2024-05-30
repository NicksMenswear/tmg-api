"""added is active to roles table

Revision ID: a1cd0e119c50
Revises: 356c3889f8f9
Create Date: 2024-05-30 10:37:50.047077

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1cd0e119c50"
down_revision: Union[str, None] = "356c3889f8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # added column
    op.add_column("roles", sa.Column("is_active", sa.Boolean(), nullable=True))

    # set to active
    op.execute("UPDATE roles SET is_active = TRUE")

    # set not nullable
    op.alter_column("roles", "is_active", nullable=False)

    # create index
    op.create_index(op.f("ix_roles_is_active"), "roles", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_roles_is_active"), table_name="roles")
    op.drop_column("roles", "is_active")
