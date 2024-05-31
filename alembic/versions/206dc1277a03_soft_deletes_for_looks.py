"""soft_deletes for looks

Revision ID: 206dc1277a03
Revises: 7016ddb603c9
Create Date: 2024-05-31 14:52:07.093422

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "206dc1277a03"
down_revision: Union[str, None] = "7016ddb603c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # added column
    op.add_column("looks", sa.Column("is_active", sa.Boolean(), nullable=True))

    # set to active
    op.execute("UPDATE looks SET is_active = TRUE")

    # set not nullable
    op.alter_column("looks", "is_active", nullable=False)

    # create index
    op.create_index(op.f("ix_looks_is_active"), "looks", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_looks_is_active"), table_name="roles")
    op.drop_column("looks", "is_active")
