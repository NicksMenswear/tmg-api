import logging
import os
from typing import Any

import requests
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

SKU_TO_VARIANT_GIDS_MAPPING = dict()


def _admin_api_graphql_request(query: str, variables: dict[str, Any] = None) -> dict[str, Any]:
    response = requests.post(
        ADMIN_API_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        raise Exception(f"Shopify API error: {response.status_code}, {str(response.text)}")

    response_data = response.json()

    if "errors" in response_data:
        raise Exception(f"Shopify API error: {response.status_code}, {str(response.text)}")

    return response_data


def get_variant_gid_by_sku(sku: str) -> str:
    query = f"""
    {{
      productVariants(first: 1, query: "sku:{sku}") {{
        edges {{
          node {{
            id
            title
            sku
            price
            product {{
              id
              title
              images(first: 1) {{
                edges {{
                  node {{
                    url
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """

    response_data = _admin_api_graphql_request(query)

    if not response_data.get("data", {}).get("productVariants", {}).get("edges"):
        raise Exception(f"Variant with SKU {sku} not found")

    return response_data["data"]["productVariants"]["edges"][0]["node"]["id"]


def shopify_remove_all_bundle_variant_relationships(parent_product_shopify_variant_gid: str):
    mutation = """
        mutation UpdateBundleComponents($input: [ProductVariantRelationshipUpdateInput!]!) {
          productVariantRelationshipBulkUpdate(input: $input) {
            parentProductVariants {
              id
              productVariantComponents(first: 10) {
                nodes{
                  id
                  quantity
                  productVariant {
                    id
                  }
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
    variables = {
        "input": [
            {
                "parentProductVariantId": parent_product_shopify_variant_gid,
                "removeAllProductVariantRelationships": True,
            }
        ]
    }

    response = requests.post(
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        logger.error(f"Failed to remove all bundle variant relationships: {response.text}")
        return

    data = response.json().get("data", {}).get("productVariantRelationshipBulkUpdate", {})

    if data.get("userErrors"):
        logger.error(f"Failed to remove all bundle variant relationships: {data['userErrors']}")
        return

    logger.info("Successfully removed all bundle variant relationships")


def shopify_add_new_variant_relationships(parent_product_shopify_variant_gid: str, variant_gids: list[str]):
    bundle_variants = [{"id": variant_gid, "quantity": 1} for variant_gid in variant_gids]

    mutation = """
        mutation CreateBundleComponents($input: [ProductVariantRelationshipUpdateInput!]!) {
          productVariantRelationshipBulkUpdate(input: $input) {
            parentProductVariants {
              id
              productVariantComponents(first: 10) {
                nodes{
                  id
                  quantity
                  productVariant {
                    id
                  }
                }
              }
            }
            userErrors {
              field
              message
            }
          }
        }
        """
    variables = {
        "input": [
            {
                "parentProductVariantId": parent_product_shopify_variant_gid,
                "productVariantRelationshipsToCreate": bundle_variants,
            }
        ]
    }

    response = requests.post(
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        logger.error(f"Failed to add new variant relationships: {response.text}")
        return

    data = response.json().get("data", {}).get("productVariantRelationshipBulkUpdate", {})

    if data.get("userErrors"):
        logger.error(f"Failed to add new variant relationships: {data['userErrors']}")
        return

    logger.info("Successfully added new variant relationships")


def shopify_update_product_active_status(product_gid: str):
    mutation = """
        mutation UpdateProductActiveStatus($input: ProductInput!) {
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
    variables = {"input": {"id": product_gid, "status": "ACTIVE"}}

    response = requests.post(
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        logger.error(f"Failed to update product active status: {response.text}")
        return

    data = response.json().get("data", {}).get("productUpdate", {})

    if data.get("userErrors"):
        logger.error(f"Failed to update product active status: {data['userErrors']}")
        return

    logger.info("Successfully updated product active status")


def get_active_looks() -> list:
    rows = session.execute(
        text(
            f"""
                SELECT id, product_specs
                FROM looks
                WHERE is_active
                  AND not fixed
                  AND (product_specs::TEXT LIKE '%703A4BLK%' OR product_specs::TEXT LIKE '%703A4COG%' OR product_specs::TEXT LIKE '%803A4BLK%' OR product_specs::TEXT LIKE '%803A4COG%')
                ORDER BY created_at DESC;
                """
        )
    ).fetchall()

    return [(row[0], row[1]) for row in rows]


def update_look_fixed_status(look_id: str):
    session.execute(
        text(
            f"""
                UPDATE looks
                SET fixed = TRUE
                WHERE id = '{look_id}';
                """
        )
    )
    session.commit()


def main():
    sku_to_variant_gids_cache = dict()

    looks = get_active_looks()

    for look_id, product_spec in looks:
        logger.info(f"Processing look {look_id}: ===============================================")

        if not product_spec:
            logger.info(f"Product specs not found for look {look_id}")
            continue

        bundle_product_id = product_spec.get("bundle", {}).get("product_id")
        bundle_variant_id = product_spec.get("bundle", {}).get("variant_id")

        if not bundle_product_id or not bundle_variant_id:
            logger.info(f"No bundle product or variant found for look {look_id}")
            continue

        items = product_spec.get("items", [])

        if not items:
            logger.info(f"No items found for look {look_id}")
            continue

        try:
            skus = [item.get("sku", item.get("variant_sku")) for item in items]
            skus.sort()

            variant_gids = []

            for sku in skus:
                variant_gid = sku_to_variant_gids_cache.get(sku, get_variant_gid_by_sku(sku))
                variant_gids.append(variant_gid)
                sku_to_variant_gids_cache[sku] = variant_gid

            shopify_remove_all_bundle_variant_relationships(f"gid://shopify/ProductVariant/{bundle_variant_id}")
            shopify_add_new_variant_relationships(f"gid://shopify/ProductVariant/{bundle_variant_id}", variant_gids)
            shopify_update_product_active_status(f"gid://shopify/Product/{bundle_product_id}")
            update_look_fixed_status(str(look_id))
        except Exception as e:
            logger.error(f"Failed to update bundle for look {look_id}: {str(e)}")
            continue


if __name__ == "__main__":
    main()
