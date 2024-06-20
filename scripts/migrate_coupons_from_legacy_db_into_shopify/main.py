import json
import logging
import os
import datetime

import urllib3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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

engine = create_engine(LEGACY_DB_URI)
Session = sessionmaker(bind=engine)
session = Session()


def create_discount_code(
    title: str,
    code: str,
    amount: float,
    coupon_type: str,
    usage_limit: int,
    start_date: datetime.date,
    end_date: datetime.date,
):
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

    if coupon_type == "percentage":
        customer_gets_value = {"percentage": amount / 100}
    elif coupon_type == "fixed_amount":
        customer_gets_value = {"discountAmount": {"amount": amount, "appliesOnEachItem": False}}
    else:
        raise ValueError("Invalid coupon type")

    variables = {
        "basicCodeDiscount": {
            "title": title,
            "code": code,
            "usageLimit": usage_limit,
            "startsAt": start_date.isoformat(),
            "endsAt": end_date.isoformat(),
            "customerSelection": {"all": True},
            "combinesWith": {"orderDiscounts": True, "productDiscounts": True, "shippingDiscounts": True},
            "customerGets": {"value": customer_gets_value, "items": {"all": True}},
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
        return response

    data = json.loads(response.data.decode("utf-8")).get("data", {})

    if "errors" in data:
        logger.error(f"Failed to create discount code {code}: {data['errors']}")
        return data

    if len(data.get("discountCodeBasicCreate", {}).get("userErrors")) > 0:
        logger.warning(f"Failed to create discount code: {data['discountCodeBasicCreate']['userErrors']}. Skipping ...")
        return data

    logger.info(f"Successfully created discount code {code}")

    return data


def fetch_not_used_coupons():
    try:
        rows = session.execute(
            text(
                """
                SELECT name, coupon_code, type, amount, apply_count, quantity, start_date, end_date
                FROM suits_coupon
                WHERE end_date >= now() AND apply_count < quantity
                ORDER BY start_date DESC
                """
            )
        )

        coupons = []

        for row in rows:
            coupons.append(
                {
                    "name": row[0],
                    "code": row[1],
                    "type": row[2],
                    "amount": row[3],
                    "usage_limit": row[5] - row[4],
                    "start_date": row[6],
                    "end_date": row[7],
                }
            )

        return coupons
    except Exception as e:
        logger.error(f"Error fetching coupons: {e}")
        return []
    finally:
        session.close()


def main():
    coupons = fetch_not_used_coupons()

    for coupon in coupons:
        create_discount_code(
            title=coupon["name"],
            code=coupon["code"],
            amount=coupon["amount"],
            coupon_type=coupon["type"],
            usage_limit=coupon["usage_limit"],
            start_date=coupon["start_date"],
            end_date=coupon["end_date"],
        )


if __name__ == "__main__":
    main()
