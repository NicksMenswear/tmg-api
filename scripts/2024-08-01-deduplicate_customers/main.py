import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = "tmg-db-prd-01.cx48ra7hy3wh.us-east-1.rds.amazonaws.com"
DB_NAME = "tmg"
DB_USER = "dbadmin"
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()


def de_duplicate_users():
    users = session.execute(
        text(
            """
            SELECT id, legacy_id, first_name, last_name, email, phone_number, shopify_id, created_at
            FROM users
            WHERE LOWER(email) IN (
                SELECT LOWER(email)
                FROM users
                GROUP BY LOWER(email)
                HAVING COUNT(*) > 1
                LIMIT 1
            )
            ORDER BY legacy_id ASC, shopify_id ASC;
            """
        )
    ).fetchall()

    if len(users) != 2:
        raise Exception("Expected 2 users with the same email")

    user1 = dict(users[0]._mapping)
    user2 = dict(users[1]._mapping)

    logger.info(f"User 1: {user1}")
    logger.info(f"User 2: {user2}")

    # if not user1.get("shopify_id"):
    #     raise Exception("User 1 doesn't have shopify_id")
    #
    if user2.get("legacy_id"):
        raise Exception("User 2 has legacy_id")

    # if user2.get("shopify_id"):
    #     raise Exception("User 2 has shopify_id")
    #
    if user1.get("first_name").lower().strip() != user2.get("first_name").lower().strip():
        raise Exception("First names don't match")

    if user1.get("last_name").lower().strip() != user2.get("last_name").lower().strip():
        raise Exception("Last names don't match")

    addresses = session.execute(
        text(
            f"""
            SELECT address_type, address_line1, city, state, zip_code, country FROM addresses WHERE user_id IN ('{user1.get("id")}', '{user2.get("id")}');
            """
        )
    ).fetchall()

    if len(addresses) != 2:
        raise Exception("Expected 2 addresses")

    address1 = dict(addresses[0]._mapping)
    address2 = dict(addresses[1]._mapping)

    logger.info(f"Address 1: {address1}")
    logger.info(f"Address 2: {address2}")

    if (
        address1.get("address_type") != address2.get("address_type")
        or address1.get("address_line1").lower().strip() != address2.get("address_line1").lower().strip()
        or address1.get("city").lower().strip() != address2.get("city").lower().strip()
        # or address1.get("state").strip() != address2.get("state").strip()
        or address1.get("zip_code").lower().strip() != address2.get("zip_code").lower().strip()
    ):
        raise Exception("Addresses doesn't match")

    try:
        # set all orders for user 2 to user 1
        session.execute(
            text(
                f"""
                UPDATE orders SET user_id = '{user1.get("id")}' WHERE user_id = '{user2.get("id")}';
                """
            )
        )

        # delete addresses for user 2
        session.execute(
            text(
                f"""
                DELETE FROM addresses WHERE user_id = '{user2.get("id")}';
                """
            )
        )

        # delete user 2
        session.execute(
            text(
                f"""
                DELETE FROM users WHERE id = '{user2.get("id")}';
                """
            )
        )

        session.commit()
    except Exception as e:
        logger.exception(e)

        session.rollback()


def main():
    while True:
        de_duplicate_users()


if __name__ == "__main__":
    main()
