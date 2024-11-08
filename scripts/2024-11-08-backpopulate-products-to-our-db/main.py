import logging
import os
import time
from typing import Any

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_HOST = "tmg-db-prd-01.cx48ra7hy3wh.us-east-1.rds.amazonaws.com"
DB_NAME = "tmg"
DB_USER = "dbadmin"
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.environ["SHOPIFY_ADMIN_API_ACCESS_TOKEN"]
SHOPIFY_STORE_NAME = os.environ["SHOPIFY_STORE_NAME"]
ADMIN_API_URL = f"https://{SHOPIFY_STORE_NAME}.myshopify.com/admin/api/2024-01/graphql.json"
TRIGGER_WEBHOOK_TAG = "trigger_webhook"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SKU_TO_VARIANT_GIDS_MAPPING = dict()


def _admin_api_graphql_request(query: str, variables: dict[str, Any] = None) -> dict[str, Any]:
    response = requests.post(
        ADMIN_API_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        raise Exception(f"Shopify API error: {response.status_code}, {str(response.text)}")

    data = response.json()

    if "errors" in data:
        raise Exception(f"Shopify API error: {response.status_code}, {str(response.text)}")

    return data


def fetch_products_page(after_cursor=None):
    query = """
    query getProducts($after: String) {
      products(first: 250, after: $after) {
        edges {
          node {
            id
            tags
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """

    variables = {"after": after_cursor}
    data = _admin_api_graphql_request(query, variables)

    return data["data"]["products"]


def fetch_all_not_tagged_products() -> list[str]:
    result = []

    after_cursor = None

    while True:
        # time.sleep(1)  # be nice to the API

        try:
            products = fetch_products_page(after_cursor)
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            time.sleep(5)
            continue  # basically retry in 5 seconds

        if not products.get("edges"):
            continue

        for edge in products.get("edges"):
            product = edge.get("node")
            tags = product.get("tags")

            if TRIGGER_WEBHOOK_TAG not in tags:  # and "hidden" not in tags:
                result.append(product["id"])

        page_info = products.get("pageInfo", {})

        if not page_info.get("hasNextPage"):
            break

        after_cursor = page_info["endCursor"]

    return result


def fetch_all_tagged_products() -> list[str]:
    result = []

    after_cursor = None

    while True:
        time.sleep(0.5)  # be nice to the API

        try:
            products = fetch_products_page(after_cursor)
        except Exception as e:
            logger.error(f"Failed to fetch products: {e}")
            time.sleep(5)
            continue  # basically retry in 5 seconds

        if not products.get("edges"):
            continue

        for edge in products.get("edges"):
            product = edge.get("node")
            tags = product.get("tags")

            if TRIGGER_WEBHOOK_TAG in tags:
                result.append(product["id"])

        page_info = products.get("pageInfo", {})

        if not page_info.get("hasNextPage"):
            break

        after_cursor = page_info["endCursor"]

    return result


def add_tags(shopify_gid: str, tags: set[str]) -> None:
    query = """
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

    variables = {
        "id": shopify_gid,
        "tags": ",".join(list(tags)),
    }

    try:
        _admin_api_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Failed to add tags in shopify store.")


def remove_tags(shopify_gid: str, tags: set[str]) -> None:
    query = """
        mutation removeTags($id: ID!, $tags: [String!]!) {
            tagsRemove(id: $id, tags: $tags) {
                node {
                    id
                }
                userErrors {
                    message
                }
            }
        }
    """

    variables = {
        "id": shopify_gid,
        "tags": ",".join(list(tags)),
    }

    try:
        _admin_api_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Failed to remove tags in shopify store.")


def main():
    logger.info("Starting the back populating process")

    # products = fetch_all_not_tagged_products()
    #
    # logger.info(f"Found {len(products)} products")
    #
    # for product_gid in products:
    #     logger.info(f"Adding tag to product {product_gid}")
    #     time.sleep(0.5)
    #     add_tags(product_gid, {TRIGGER_WEBHOOK_TAG})

    products = fetch_all_tagged_products()

    for product_gid in products:
        logger.info(f"Removing tag from product {product_gid}")
        time.sleep(0.5)
        remove_tags(product_gid, {TRIGGER_WEBHOOK_TAG})


if __name__ == "__main__":
    main()
