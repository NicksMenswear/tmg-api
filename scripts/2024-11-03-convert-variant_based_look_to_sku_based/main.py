import logging
import os
import random
from typing import Any
from uuid import UUID

import requests
from sqlalchemy import create_engine, text, bindparam
from sqlalchemy.dialects.postgresql import JSON
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


def _admin_api_graphql_request(query: str, variables: dict[str, Any] = None) -> dict[str, Any]:
    response = requests.post(
        ADMIN_API_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        raise Exception(f"Shopify API error: {response.status_code}, {response.text}")

    response_data = response.json()

    if "errors" in response_data:
        raise Exception(f"Shopify API error: {response.status_code}, {str(response.text)}")

    return response_data


def get_active_looks() -> list[tuple[UUID, dict]]:
    rows = session.execute(
        text(
            f"""
            SELECT id, product_specs_legacy
            FROM looks
            WHERE is_active
              AND product_specs_legacy IS NOT NULL
              AND (product_specs -> 'bundle' ->> 'sku') IS NULL;
            """
        )
    ).fetchall()

    return [(row[0], row[1]) for row in rows]


def get_variant_by_id(variant_gid: str) -> dict[str, Any]:
    query = """
        query getProductVariantAndProduct($variantId: ID!) {
            node(id: $variantId) {
                ... on ProductVariant {
                    id
                    title
                    sku
                    price
                    product {
                        id
                        title
                        tags
                    }
                }
            }
        }
    """

    variables = {"variantId": variant_gid}

    body = _admin_api_graphql_request(query, variables)

    return body.get("data", {}).get("node", {})


def add_sku_to_variant(variant_id: str, sku: str) -> None:
    query = """
        mutation productVariantUpdate($input: ProductVariantInput!) {
          productVariantUpdate(input: $input) {
            product {
              id
              title
              tags
              variants(first: 1) {
                edges {
                  node {
                    id
                    title
                    price
                    sku
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
        "input": {
            "id": f"gid://shopify/ProductVariant/{variant_id}",
            "sku": sku,
        }
    }

    response = requests.post(
        ADMIN_API_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        logger.error(f"Failed to update variant {variant_id}: {response.text}")
        return

    data = response.json().get("data", {}).get("productVariantUpdate", {})

    if data.get("userErrors"):
        logger.error(f"Failed to update variant {variant_id}: {data['userErrors']}")


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


def update_product_specs(look_id: UUID, new_product_specs: dict) -> None:
    try:
        session.execute(
            text(
                """
                    UPDATE looks
                    SET product_specs = :new_product_specs
                    WHERE id = :look_id;
                    """
            ).bindparams(
                bindparam("new_product_specs", value=new_product_specs, type_=JSON),
                bindparam("look_id", value=look_id),
            )
        )
        session.commit()
    except Exception as e:
        logger.error(f"Failed to update product specs for look {look_id}: {e}")
        session.rollback()


def main():
    looks = get_active_looks()

    for look_id, product_spec in looks:
        logger.info(f"Processing look {look_id}: ===============================================")

        if (
            not product_spec
            or not product_spec.get("bundle")
            or not product_spec.get("suit")
            or not product_spec.get("items")
        ):
            logger.error(f"Product spec {product_spec} does not have a bundle, suit or items")
            continue

        product_id = product_spec.get("bundle", {}).get("product_id")
        variant_id = product_spec.get("bundle", {}).get("variant_id")
        items = product_spec.get("items", [])

        if not product_id or not variant_id:
            logger.error(
                f"Product spec {product_spec} does not have a bundle.product_id or bundle.variant_id. Must be a legacy look"
            )
            continue

        shopify_variant = get_variant_by_id(f"gid://shopify/ProductVariant/{variant_id}")

        if "userErrors" in shopify_variant:
            logger.error(f"Failed to get variant {variant_id}: {shopify_variant['userErrors']}")
            deactivate_looks_that_have_product_that_does_not_exist(look_id)
            continue

        bundle_identifier = None

        for item in items:
            if item.get("variant_sku", "").startswith("bundle-"):
                bundle_identifier = item.get("variant_sku", "").removeprefix("bundle-")
                break

        if not bundle_identifier and shopify_variant.get("product", {}).get("title", "").startswith("Suit Bundle #"):
            bundle_identifier = shopify_variant.get("product", {}).get("title", "").removeprefix("Suit Bundle #")

        if shopify_variant.get("sku"):
            look_sku = shopify_variant.get("sku")
        else:
            if bundle_identifier:
                look_sku = f"suit-bundle-{bundle_identifier}"
            else:
                bundle_identifier = str(random.randint(100000, 1000000000))
                look_sku = f"suit-bundle-{bundle_identifier}"

            add_sku_to_variant(variant_id, look_sku)

        new_items = []
        for item in items:
            new_items.append({"sku": item.get("variant_sku")})

        new_product_specs = {
            "bundle": {
                "product_id": product_id,
                "variant_id": variant_id,
                "sku": look_sku,
                "price": float(shopify_variant.get("price", 0.0)),
            },
            "suit": {"sku": product_spec.get("suit", {}).get("variant_sku")},
            "items": new_items,
        }

        update_product_specs(look_id, new_product_specs)

        logger.info(f"Old specs: {product_spec}")
        logger.info(f"New specs: {new_product_specs}")


if __name__ == "__main__":
    main()
