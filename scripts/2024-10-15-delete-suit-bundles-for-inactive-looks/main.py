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
MEMBER_OF_4_PLUS_EVENT_TAG = "member_of_4_plus_event"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_bundle_product_specs_for_inactive_looks() -> List[dict]:
    rows = session.execute(
        text(
            f"""
            SELECT product_specs
            FROM looks
            WHERE NOT is_active
              AND product_specs IS NOT NULL
              AND product_specs::jsonb -> 'bundle' ? 'product_id'
            ORDER BY created_at DESC;
            """
        )
    ).fetchall()

    return [row[0] for row in rows]


def archive_product(product_id: str) -> None:
    query = """
    mutation productUpdate($input: ProductInput!) {
      productUpdate(input: $input) {
        product {
          id
          status
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    product_gid = f"gid://shopify/Product/{product_id}"

    variables = {
        "input": {
            "id": product_gid,
            "status": "ARCHIVED",
        }
    }

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status >= 400:
        logger.error(f"Failed to archive product by id '{product_gid}': {response.data}")

    try:
        data = json.loads(response.data.decode("utf-8")).get("data", {})

        if "errors" in data:
            logger.error(f"Failed to archive product by id '{product_gid}': {data['errors']}")

        logger.info(f"Archived product by id '{product_gid}'")
    except Exception as e:
        logger.error(f"Failed to archive product by id '{product_gid}': {e}")


def main():
    product_specs = get_bundle_product_specs_for_inactive_looks()

    for product_spec in product_specs:
        product_id = product_spec.get("bundle", {}).get("product_id")

        if not product_id:
            logger.error(f"Product spec {product_spec} does not have a bundle.product_id")
            continue

        items = product_spec.get("items", [])

        if not items:
            archive_product(product_id)
            logger.error(f"Product spec {product_spec} does not have any items")
            continue

        has_bundle_identifier_product = False
        bundle_identifier_product_id = None

        for item in items:
            sku = item.get("variant_sku")
            bundle_identifier_product_id = item.get("product_id")

            if not sku:
                logger.error(f"Item {item} does not have a variant_sku")
                continue

            if sku.startswith("bundle-"):
                bundle_identifier_product_id = item.get("product_id")
                has_bundle_identifier_product = True
                break

        archive_product(product_id)

        if has_bundle_identifier_product:
            archive_product(bundle_identifier_product_id)


if __name__ == "__main__":
    main()
