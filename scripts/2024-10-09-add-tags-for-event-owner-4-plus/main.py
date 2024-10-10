import json
import logging
import os
from typing import List

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
EVENT_OWNER_4_PLUS_TAG = "event_owner_4_plus"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_shopify_customer_ids_that_have_4_plus_attendee_in_events() -> List[int]:
    rows = session.execute(
        text(
            f"""
            SELECT DISTINCT(u2.shopify_id)
            FROM events e2
            JOIN users u2 ON u2.id = e2.user_id
            WHERE u2.shopify_id IS NOT NULL
                AND e2.id IN (
                    SELECT e.id
                    FROM events e
                    JOIN attendees a ON a.event_id = e.id
                    WHERE e.is_active
                      AND a.is_active
                      AND a.invite
                      AND e.event_at > '2024-10-09T00:00:00'
                    GROUP BY e.id
                    HAVING count(a.id) >= 4
                );
            """
        )
    ).fetchall()

    return [int(row[0]) for row in rows]


def add_tag_to_customer_by_id(shopify_customer_id: int) -> None:
    shopify_customer_gid = f"gid://shopify/Customer/{shopify_customer_id}"

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

    variables = {"id": shopify_customer_gid, "tags": [EVENT_OWNER_4_PLUS_TAG]}

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status >= 400:
        logger.error(f"Failed to add tag {EVENT_OWNER_4_PLUS_TAG} to customer {shopify_customer_gid}: {response.data}")
        raise Exception(f"Failed to add tag {EVENT_OWNER_4_PLUS_TAG} to customer {shopify_customer_gid}")

    data = json.loads(response.data.decode("utf-8")).get("data", {})

    if "errors" in data:
        logger.error(f"Failed to add tag {EVENT_OWNER_4_PLUS_TAG} to customer {shopify_customer_gid}: {data['errors']}")
        raise Exception(f"Failed to add tag {EVENT_OWNER_4_PLUS_TAG} to customer {shopify_customer_gid}")

    logger.info(f"Successfully added tag {EVENT_OWNER_4_PLUS_TAG} to customer {shopify_customer_gid}")


def main():
    customers = get_shopify_customer_ids_that_have_4_plus_attendee_in_events()

    for shopify_customer_id in customers:
        add_tag_to_customer_by_id(shopify_customer_id)


if __name__ == "__main__":
    main()
