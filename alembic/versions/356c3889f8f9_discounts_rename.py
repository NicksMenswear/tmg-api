"""discounts_rename

Revision ID: 356c3889f8f9
Revises: 9a58c605c434
Create Date: 2024-05-28 17:55:14.353491

"""

from typing import Sequence, Union

from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "356c3889f8f9"
down_revision: Union[str, None] = "9a58c605c434"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a temporary type with the new enum values
    new_discounttype = postgresql.ENUM("GIFT", "FULL_PAY", "PARTY_OF_FOUR", name="new_discounttype")
    new_discounttype.create(op.get_bind(), checkfirst=True)

    # Rename existing values
    op.execute("UPDATE discounts SET type = 'GIFT' WHERE type = 'GROOM_GIFT'")
    op.execute("UPDATE discounts SET type = 'FULL_PAY' WHERE type = 'GROOM_FULL_PAY'")

    # Alter the column to use the new enum type
    op.execute("ALTER TABLE discounts ALTER COLUMN type TYPE new_discounttype USING type::text::new_discounttype")

    # Drop old enum type
    op.execute("DROP TYPE discounttype")

    # Rename
    op.execute("ALTER TYPE new_discounttype RENAME TO discounttype")


def downgrade() -> None:
    # Create a temporary type with the old enum values
    old_discounttype = postgresql.ENUM("GROOM_GIFT", "GROOM_FULL_PAY", "PARTY_OF_FOUR", name="old_discounttype")
    old_discounttype.create(op.get_bind(), checkfirst=True)

    # Rename existing values back to the original ones
    op.execute("UPDATE discounts SET type = 'GROOM_GIFT' WHERE type = 'GIFT'")
    op.execute("UPDATE discounts SET type = 'GROOM_FULL_PAY' WHERE type = 'FULL_PAY'")

    # Alter the column to use the old enum type
    op.execute("ALTER TABLE discounts ALTER COLUMN type TYPE old_discounttype USING type::text::old_discounttype")

    # Drop the new enum type
    op.execute("DROP TYPE discounttype")

    # Rename the old enum type to the original enum type name
    op.execute("ALTER TYPE old_discounttype RENAME TO discounttype")
