import json
import logging
import os
from datetime import datetime, timezone
from typing import Set, Dict

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
# CUSTOMERS_CSV_FILE = "customers.csv"
CUSTOMERS_CSV_FILE = "customers-test.csv"
# DISCOUNT_CODE = "$100FORYOU"
DISCOUNT_CODE = "100OFF-ZINOVII-TEST"
PROMO_TAG = "PROMO-OCT24-100OFF"
SHOPIFY_CUSTOMER_SEGMENT_GID = "gid://shopify/Segment/457939615786"  # PROMO-OCT24-100OFF

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_customers_from_db(emails: Set[str]) -> Dict[str, int]:
    csv_emails = ",".join([f"'{email}'" for email in emails])

    rows = session.execute(
        text(
            f"""
            SELECT email, shopify_id
            FROM users
            WHERE LOWER(email) in ({csv_emails}) and shopify_id is not null
            """
        )
    ).fetchall()

    customers: Dict[str, int] = {}

    for row in rows:
        customers[row[0]] = int(row[1])

    return customers


def create_discount_code_for_100usd(code: str) -> str:
    mutation = """
        mutation discountCodeBasicCreate($basicCodeDiscount: DiscountCodeBasicInput!) {
          discountCodeBasicCreate(basicCodeDiscount: $basicCodeDiscount) {
            userErrors {
              field
              message
            }
            codeDiscountNode {
              id
              codeDiscount {
                ... on DiscountCodeBasic {
                  title
                  codes(first: 3) {
                    nodes {
                      code
                    }
                  }
                }
              }
            }
          }
        }
        """

    variables = {
        "basicCodeDiscount": {
            "title": code,
            "code": code,
            "startsAt": datetime.now(timezone.utc).isoformat(),
            "appliesOncePerCustomer": True,
            "customerSelection": {"customerSegments": {"add": [SHOPIFY_CUSTOMER_SEGMENT_GID]}},
            "combinesWith": {"orderDiscounts": True},
            "minimumRequirement": {"subtotal": {"greaterThanOrEqualToSubtotal": 301.00}},
            "customerGets": {
                "value": {"discountAmount": {"amount": 100.00, "appliesOnEachItem": False}},
                "items": {"all": True},
            },
        }
    }

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status >= 400:
        logger.error(f"Failed to create discount code {code}: {response.json()}")
        raise Exception(f"Failed to create discount code {code}")

    data = json.loads(response.data.decode("utf-8")).get("data", {})

    if "errors" in data:
        logger.error(f"Failed to create discount code {code}: {data['errors']}")
        raise Exception(f"Failed to create discount code {code}")

    logger.info(f"Successfully created discount code {code}")

    return data.get("discountCodeBasicCreate", {}).get("codeDiscountNode", {}).get("id")


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

    variables = {"id": shopify_customer_gid, "tags": [PROMO_TAG]}

    response = urllib3.PoolManager().request(
        "POST",
        ADMIN_API_URL,
        json={"query": mutation, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status >= 400:
        logger.error(f"Failed to add tag {PROMO_TAG} to customer {shopify_customer_gid}: {response.data}")
        raise Exception(f"Failed to add tag {PROMO_TAG} to customer {shopify_customer_gid}")

    data = json.loads(response.data.decode("utf-8")).get("data", {})

    if "errors" in data:
        logger.error(f"Failed to add tag {PROMO_TAG} to customer {shopify_customer_gid}: {data['errors']}")
        raise Exception(f"Failed to add tag {PROMO_TAG} to customer {shopify_customer_gid}")

    logger.info(f"Successfully added tag {PROMO_TAG} to customer {shopify_customer_gid}")


def read_customers_from_csv_file(file_path: str) -> Set[str]:
    with open(file_path, "r") as file:
        lines = file.readlines()

    customers = set()

    for line in lines[1:]:
        line = line.strip()
        items = line.split(",")

        email = items[0]

        if not email:
            continue

        customers.add(email.lower())

    return customers


def main():
    customers = read_customers_from_csv_file(CUSTOMERS_CSV_FILE)
    customers_map = get_customers_from_db(customers)
    shopify_customer_ids = list(customers_map.values())
    create_discount_code_for_100usd(DISCOUNT_CODE)

    for shopify_customer_id in shopify_customer_ids:
        add_tag_to_customer_by_id(shopify_customer_id)


if __name__ == "__main__":
    main()
