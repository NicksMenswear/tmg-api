import json
import logging
import os
import uuid
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
MEMBER_OF_4_PLUS_EVENT_TAG = "member_of_4_plus_event"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# find all looks that are active
# get their product specs
# if product has bundle.product_id
# figure out items
# add tags to that product by id


def get_bundle_product_specs_for_active_looks() -> List[dict]:
    rows = session.execute(
        text(
            f"""
            SELECT product_specs
            FROM looks
            WHERE is_active
              AND product_specs IS NOT NULL
              AND product_specs::jsonb -> 'bundle' ? 'product_id'\
            ORDER BY created_at DESC;
            """
        )
    ).fetchall()

    return [row[0] for row in rows]


def add_tags_to_product(product_id: int, tags: list[str]) -> None:
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
        # raise Exception(f"Failed to add tags {tags} to product {product_gid}")

    data = json.loads(response.data.decode("utf-8")).get("data", {})

    if "errors" in data:
        logger.error(f"Failed to add tags {tags} to product {product_gid}: {data['errors']}")
        # raise Exception(f"Failed to add tag {MEMBER_OF_4_PLUS_EVENT_TAG} to customer {shopify_customer_gid}")

    logger.info(f"Successfully added tags {tags} to product {product_gid}")


def main():
    product_specs = get_bundle_product_specs_for_active_looks()

    for product_spec in product_specs:
        product_id = product_spec.get("bundle", {}).get("product_id")

        if not product_id:
            logger.error(f"Product spec {product_spec} does not have a bundle.product_id")
            continue

        items = product_spec.get("items", [])

        if not items:
            logger.error(f"Product spec {product_spec} does not have any items")
            continue

        tags = set()
        tags.add("suit_bundle")

        for item in items:
            sku = item.get("variant_sku")

            if not sku:
                logger.error(f"Item {item} does not have a variant_sku")
                continue

            if sku.startswith("4"):
                tags.add("has_shirt")
            elif sku.startswith("5"):
                tags.add("has_bow_tie")
                tags.add("has_tie")
            elif sku.startswith("6"):
                tags.add("has_tie")
                tags.add("has_neck_tie")
            elif sku.startswith("7"):
                tags.add("has_belt")
            elif sku.startswith("8"):
                tags.add("has_shoes")
            elif sku.startswith("9"):
                tags.add("has_socks")
            elif sku.startswith("P"):
                tags.add("has_premium_pocket_square")

        tags = list(tags)

        add_tags_to_product(product_id, tags)


if __name__ == "__main__":
    main()
