import json
import logging
import os
from uuid import UUID

import urllib3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_HOST = "tmg-db-prd-01.cx48ra7hy3wh.us-east-1.rds.amazonaws.com"
DB_NAME = "tmg"
DB_USER = "dbadmin"
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.environ["SHOPIFY_ADMIN_API_ACCESS_TOKEN"]
SHOPIFY_STORE_NAME = os.environ["SHOPIFY_STORE_NAME"]
ADMIN_API_URL = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2024-01/graphql.json"

TAG_PRODUCT_NOT_LINKED_TO_EVENT = "not_linked_to_event"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_looks_that_are_not_linked_to_event() -> list[tuple[UUID, dict]]:
    rows = session.execute(
        text(
            f"""
            SELECT l2.id, l2.product_specs FROM looks l2 WHERE l2.id IN (
                SELECT distinct(l1.id)
                FROM looks l1
                WHERE l1.is_active 
                  AND l1.id NOT IN (
                    SELECT distinct(a.look_id)
                    FROM attendees a
                    JOIN events e ON e.id=a.event_id
                    WHERE a.is_active 
                      AND e.is_active 
                      AND a.look_id IS NOT NULL
                  )
            );
            """
        )
    ).fetchall()

    return [(row[0], row[1]) for row in rows]


def deactivate_looks_that_have_product_that_does_not_exist(look_id: UUID) -> None:
    try:
        session.execute(
            text(
                f"""
                UPDATE looks
                SET is_active = FALSE
                WHERE id = :look_id;
                """
            ),
            {"look_id": str(look_id)},
        )
        session.commit()
    except Exception as e:
        logger.error(f"Failed to deactivate look {look_id}: {e}")
        session.rollback()


def add_tags_to_product(look_id: UUID, product_id: int, tags: list[str]) -> None:
    product_gid = f"gid://shopify/Product/{product_id}"

    mutation = """
        mutation addTags($id: ID!, $tags: [String!]!) {
            tagsAdd(id: $id, tags: $tags) {
                node {
                    id
                }
                userErrors {
                    message
                }
              }
            }
            """

    variables = {"id": product_gid, "tags": tags}

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status >= 400:
        logger.error(f"Failed to add tags {tags} to product {product_gid}: {response.data}")

    try:
        data = json.loads(response.data.decode("utf-8")).get("data", {})

        if "errors" in data:
            logger.error(f"Failed to add tags {tags} to product {product_gid}: {data['errors']}")

        if data.get("tagsAdd", {}).get("userErrors", []):
            user_errors = data["tagsAdd"]["userErrors"]

            if user_errors and user_errors[0].get("message") == "Product does not exist":
                deactivate_looks_that_have_product_that_does_not_exist(look_id)
            else:
                logger.error(f"Failed to add tags {tags} to product {product_gid}: {user_errors}")
                return

        logger.info(f"Successfully added tags {tags} to product {product_gid}")
    except Exception as e:
        logger.error(f"Failed to add tags {tags} to product {product_gid}: {e}")


def main():
    looks = get_looks_that_are_not_linked_to_event()

    for look_id, product_spec in looks:
        product_id = product_spec.get("bundle", {}).get("product_id")

        if not product_id:
            logger.error(f"Product spec {product_spec} does not have a bundle.product_id")
            continue

        add_tags_to_product(look_id, product_id, [TAG_PRODUCT_NOT_LINKED_TO_EVENT])


if __name__ == "__main__":
    main()
