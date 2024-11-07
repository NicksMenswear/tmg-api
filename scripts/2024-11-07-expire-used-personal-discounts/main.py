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


def shopify_deactivate_discount(discount_gid: str):
    query = """
    mutation discountCodeDeactivate($id: ID!) {
      discountCodeDeactivate(id: $id) {
        codeDiscountNode {
          codeDiscount {
            ... on DiscountCodeBasic {
              title
              status
              startsAt
              endsAt
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

    variables = {"id": discount_gid}

    response = requests.post(
        ADMIN_API_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        logger.error(f"Failed to update discount: {response.text}")
        return

    data = response.json().get("data", {}).get("productUpdate", {})

    if data.get("userErrors"):
        logger.error(f"Failed to update discount: {data['userErrors']}")
        return

    logger.info("Successfully updated discount")


def get_used_personal_discounts() -> list:
    rows = session.execute(
        text(
            f"""
                SELECT shopify_discount_code_id, shopify_discount_code
                FROM discounts
                WHERE used
                  AND shopify_discount_code IS NOT NULL
                  AND (shopify_discount_code LIKE 'TMG-GROUP-%' OR shopify_discount_code LIKE 'GIFT-%')
                ORDER BY created_at DESC;
                """
        )
    ).fetchall()

    return [(row[0], row[1]) for row in rows]


def main():
    discounts = get_used_personal_discounts()

    for discount_id, discount_code in discounts:
        logger.info(
            f"Processing discount {discount_id} / {discount_code}: ==============================================="
        )

        try:
            shopify_deactivate_discount(f"gid://shopify/DiscountCodeNode/{discount_id}")
        except Exception as e:
            logger.error(f"Failed to update discount {discount_id} / {discount_code}: {e}")
            continue


if __name__ == "__main__":
    main()
