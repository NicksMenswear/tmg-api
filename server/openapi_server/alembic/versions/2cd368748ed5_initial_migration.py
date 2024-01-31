"""Initial Migration

Revision ID: 2cd368748ed5
Revises: 
Create Date: 2024-01-30 19:26:03.739787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from database.models import Base

# revision identifiers, used by Alembic.
revision: str = '2cd368748ed5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
