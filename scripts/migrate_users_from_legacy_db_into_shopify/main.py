import json
import logging
import os
import uuid
from typing import Dict, Any

import urllib3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from server.database.models import User
from server.encoder import CustomJSONEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.environ["SHOPIFY_ADMIN_API_ACCESS_TOKEN"]
SHOPIFY_STORE_NAME = os.environ["SHOPIFY_STORE_NAME"]

ADMIN_API_URL = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2024-01/graphql.json"
LEGACY_DB_HOST = "production.cx48ra7hy3wh.us-east-1.rds.amazonaws.com"
LEGACY_DB_NAME = "production"
LEGACY_DB_USER = "postgres"
LEGACY_DB_PASSWORD = os.environ["LEGACY_DB_PASSWORD"]
LEGACY_DB_URI = f"postgresql+psycopg2://{LEGACY_DB_USER}:{LEGACY_DB_PASSWORD}@{LEGACY_DB_HOST}:5432/{LEGACY_DB_NAME}"

NEW_DB_HOST = os.environ["NEW_DB_HOST"]
NEW_DB_NAME = "tmg"
NEW_DB_USER = os.environ["NEW_DB_USER"]
NEW_DB_PASSWORD = os.environ["NEW_DB_PASSWORD"]
NEW_DB_URI = f"postgresql+psycopg2://{NEW_DB_USER}:{NEW_DB_PASSWORD}@{NEW_DB_HOST}:5432/{NEW_DB_NAME}"

legacy_engine = create_engine(LEGACY_DB_URI)
LegacySession = sessionmaker(bind=legacy_engine)
legacy_session = LegacySession()

new_engine = create_engine(NEW_DB_URI)
NewSession = sessionmaker(bind=new_engine)
new_session = NewSession()


def fetch_users_from_legacy_db():
    try:
        rows = legacy_session.execute(
            text(
                """
                SELECT *
                FROM users_user
                ORDER BY date_joined DESC
                LIMIT 1000
                """
            )
        ).fetchall()

        users = {}

        for row in rows:
            user = dict(row._mapping)
            email = user.get("email").lower()
            user["email"] = email
            users[email] = user

        return users
    except Exception as e:
        logger.error(f"Error fetching coupons: {e}")
        return {}
    finally:
        legacy_session.close()


def get_users_with_legacy_ids_from_new_db():
    try:
        db_users = new_session.query(User).all()

        users = {}

        for db_user in db_users:
            if not db_user.email:
                continue

            users[db_user.email.lower()] = db_user

        return users
    except Exception as e:
        logger.exception(e)
        return {}


def insert_user_into_db(legacy_user: Dict[str, Any]):
    db_user = User(
        id=uuid.uuid4(),
        legacy_id=legacy_user["id"],
        first_name=legacy_user["first_name"],
        last_name=legacy_user["last_name"],
        email=legacy_user["email"],
        phone_number=legacy_user.get("phone") if legacy_user.get("phone") else None,
        account_status=False,
        meta={"legacy": json.loads(json.dumps(legacy_user, cls=CustomJSONEncoder))},
    )

    try:
        new_session.add(db_user)
        new_session.commit()
        new_session.refresh(db_user)
    except Exception as e:
        logger.exception(e)
        new_session.rollback()

    return db_user


def create_shopify_customer_via_api(legacy_user):
    query = """
        mutation createCustomer($input: CustomerInput!) {
          customerCreate(input: $input) {
            customer {
              id
            }
            userErrors {
              field
              message
            }
          }
        }
        """

    input_data = {
        "firstName": legacy_user["first_name"],
        "lastName": legacy_user["last_name"],
        "email": legacy_user["email"],
        "tags": "legacy",
    }

    if legacy_user.get("phone"):
        if legacy_user["phone"].startswith("+1"):
            input_data["phone"] = legacy_user["phone"]
        elif len(legacy_user["phone"]) == 11:
            input_data["phone"] = "+" + legacy_user["phone"]
    else:
        input_data["phone"] = None

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        body=json.dumps({"query": query, "variables": {"input": input_data}}),
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status >= 400:
        logger.error(f"Failed to create shopify user {legacy_user['email']}: {response.json()}")
        return None

    decoded = json.loads(response.data.decode("utf-8"))
    data = decoded.get("data", {})
    extensions = decoded.get("extensions", {})

    logger.info(f"Extensions: {extensions}")

    if "userErrors" in data:
        logger.error(f"Failed to create shopify user {legacy_user['email']}: {data}")
        return None

    customer = data.get("customerCreate", {}).get("customer", {})

    if not customer or not customer.get("id", "").startswith("gid://shopify/Customer/"):
        logger.error(f"Failed to create shopify user {legacy_user['email']}: {decoded}")
        return None

    logger.info(f"Successfully created user {legacy_user['email']}")

    return customer.get("id").strip("gid://shopify/Customer/")


def get_shopify_customer_id_by_email(email):
    query = f"""
    {{
      customers(first: 1, query: "email:{email}") {{
        edges {{
          node {{
            id
            email
          }}
        }}
      }}
    }}
    """

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        body=json.dumps({"query": query}),
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    decoded = json.loads(response.data.decode("utf-8"))
    data = decoded.get("data", {})
    extensions = decoded.get("extensions", {})

    logger.info(f"Extensions: {extensions}")

    if "userErrors" in data:
        logger.error(f"Failed to get shopify user by email '{email}': {data}")
        return

    shopify_id = data.get("customers", {}).get("edges", [{}])[0].get("node", {}).get("id")
    shopify_id = shopify_id.strip("gid://shopify/Customer/")

    return shopify_id


def main():
    new_db_users = get_users_with_legacy_ids_from_new_db()
    legacy_db_users = fetch_users_from_legacy_db()

    for legacy_db_user_email in legacy_db_users.keys():
        logger.info(f"Processing user {legacy_db_user_email} ...")
        legacy_db_user = legacy_db_users[legacy_db_user_email]
        del legacy_db_user["password"]

        new_db_user = new_db_users.get(legacy_db_user["email"])

        if not new_db_user:
            logger.info(f"User by email '{legacy_db_user_email}' not found in new db. Creating ...")

            new_db_user = insert_user_into_db(legacy_db_user)
            if not new_db_user:
                logger.error(f"Failed to insert user '{legacy_db_user_email}' into new db")
                continue

            logger.info(f"User '{legacy_db_user_email}' inserted into new db with id '{new_db_user.id}'")

            logger.info(f"Creating shopify user '{legacy_db_user_email}' ...")

            shopify_id = create_shopify_customer_via_api(legacy_db_user)

            if not shopify_id:
                logger.error(f"Failed to create shopify user {legacy_db_user_email}. Skipping ...")
                continue

            logger.info(f"Shopify user '{legacy_db_user_email}' created with shopify id: '{shopify_id}'")
            logger.info(f"Updating user '{legacy_db_user_email}' with shopify id '{shopify_id}' ...")

            try:
                new_db_user.shopify_id = shopify_id
                new_session.commit()
            except Exception as e:
                logger.exception(e)
                new_session.rollback()
        else:
            if not new_db_user.shopify_id:
                logger.info(
                    f"User {legacy_db_user_email} found in new db by email but doesn't have shopify_id. Creating shopify user"
                )

                shopify_id = create_shopify_customer_via_api(legacy_db_user)

                logger.info(f"Shopify user {legacy_db_user_email} created: {shopify_id}")

                if not shopify_id:
                    logger.error(f"Failed to create shopify user {legacy_db_user_email}")
                    continue

                new_db_user.shopify_id = shopify_id

                try:
                    new_db_user.legacy_id = legacy_db_user["id"]
                    new_db_user.meta = {"legacy": json.loads(json.dumps(legacy_db_user, cls=CustomJSONEncoder))}
                    new_session.commit()
                except Exception as e:
                    logger.exception(e)
                    new_session.rollback()
            else:
                if not new_db_user.legacy_id:
                    logger.error(f"user doesn't have legacy id but has shopify id: {new_db_user.id}")
                    continue

                if new_db_user.legacy_id != str(legacy_db_user["id"]):
                    logger.error(f"Legacy id doesn't match for user {new_db_user.id}")
                    continue

                logger.info(f"User {legacy_db_user_email} already exists. Skipping ...")


if __name__ == "__main__":
    main()
