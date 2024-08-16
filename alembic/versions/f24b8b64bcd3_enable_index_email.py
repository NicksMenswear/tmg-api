"""enable index email

Revision ID: f24b8b64bcd3
Revises: f7aa37f7efe0
Create Date: 2024-05-07 16:45:03.837459

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f24b8b64bcd3"
down_revision: Union[str, None] = "f7aa37f7efe0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.create_unique_constraint("users_email_key", "users", ["email"])
    # ### end Alembic commands ###
