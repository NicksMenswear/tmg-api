"""added meta to users table and set account_status default to False

Revision ID: c059b0a38e52
Revises: 1477b09ba621
Create Date: 2024-06-26 13:56:27.604169

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c059b0a38e52"
down_revision: Union[str, None] = "1477b09ba621"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # meta
    op.add_column("users", sa.Column("meta", sa.JSON(), server_default=sa.text("'{}'::jsonb"), nullable=True))
    op.execute("UPDATE users SET meta = '{}'")
    op.alter_column("users", "meta", existing_type=sa.JSON(), nullable=False)

    # account_status
    op.execute("UPDATE users SET account_status = FALSE WHERE account_status IS NULL")
    op.alter_column("users", "account_status", existing_type=sa.BOOLEAN(), nullable=False, default=False)


def downgrade() -> None:
    op.drop_column("users", "meta")
    op.alter_column("users", "account_status", existing_type=sa.BOOLEAN(), nullable=True, default=False)
