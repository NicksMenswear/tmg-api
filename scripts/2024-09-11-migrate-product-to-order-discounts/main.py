import json
import logging
import os
from typing import List, Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.controllers.util import http
from server.database.models import Discount

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "tmg-db-dev-01.cfbqizbq9cdk.us-west-2.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "tmg")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "quickstart-a91e1214")
SHOPIFY_STORE_ADMIN_GRAPHQL_ENDPOINT = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2024-01/graphql.json"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()


def get_all_not_used_discounts() -> List[Discount]:
    return session.query(Discount).filter(Discount.used == False).order_by(Discount.created_at.desc()).all()


def shopify_admin_request(body):
    response = http(
        "POST",
        SHOPIFY_STORE_ADMIN_GRAPHQL_ENDPOINT,
        json=body,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN,
        },
    )

    if response.status >= 500:
        raise Exception(f"Shopify API error. Status code: {response.status}, message: {response.data.decode('utf-8')}")

    return response.status, json.loads(response.data.decode("utf-8"))


def get_shopify_discount_by_id(shopify_discount_code_id: int) -> Optional[Dict[str, Any]]:
    query = f"""
    query {{
      codeDiscountNode(id: "gid://shopify/DiscountCodeNode/{shopify_discount_code_id}") {{
        id
        codeDiscount {{
          ... on DiscountCodeBasic {{
            title
            summary
            shortSummary
            appliesOncePerCustomer
            status
            usageLimit
            discountClass
            combinesWith {{
              orderDiscounts
              productDiscounts
              shippingDiscounts
            }}
            customerGets {{
              appliesOnOneTimePurchase
              items {{
                __typename ... on AllDiscountItems {{
                  allItems
                }}
              }}
              value {{
                __typename 
                ... on DiscountAmount {{
                  amount {{
                    amount
                    currencyCode
                  }}
                }}
                ... on DiscountPercentage {{
                  percentage
                }}
              }}
            }}
            customerSelection {{
              __typename 
              ... on DiscountCustomers {{
                customers {{
                  id
                  email
                  firstName
                  lastName
                }}
              }}
            }}
            minimumRequirement {{
              __typename 
              ... on DiscountMinimumQuantity {{
                greaterThanOrEqualToQuantity
              }}
              ... on DiscountMinimumSubtotal {{
                greaterThanOrEqualToSubtotal {{
                  amount
                  currencyCode
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """

    status, body = shopify_admin_request({"query": query})

    if status >= 400:
        raise Exception(f"Failed to get discount by id: {body}")

    if "errors" in body:
        raise Exception(f"Failed to get discount by id: {body['errors']}")

    discount_node = body.get("data", {}).get("codeDiscountNode")

    if not discount_node:
        return None

    return discount_node.get("codeDiscount")


def update_shopify_discount(
    shopify_discount_code_id: int,
    minimum_required_amount: Optional[int] = None,
    discount_fixed_amount: Optional[int] = None,
    discount_percentage: Optional[float] = None,
) -> Dict[str, Any]:
    mutation = """
        mutation discountCodeBasicUpdate($id: ID!, $basicCodeDiscount: DiscountCodeBasicInput!) {
          discountCodeBasicUpdate(id: $id, basicCodeDiscount: $basicCodeDiscount) {
            codeDiscountNode {
              codeDiscount {
                ... on DiscountCodeBasic {
                  title
                  summary
                  shortSummary
                  appliesOncePerCustomer
                  status
                  usageLimit
                  discountClass
                  combinesWith {
                    orderDiscounts
                    productDiscounts
                    shippingDiscounts
                  }
                  customerGets {
                    appliesOnOneTimePurchase
                    items {
                      __typename ... on AllDiscountItems {
                        allItems
                      }
                    }
                    value {
                      __typename 
                      ... on DiscountAmount {
                        amount {
                          amount
                          currencyCode
                        }
                      }
                      ... on DiscountPercentage {
                        percentage
                        }
                      }
                    }
                  customerSelection {
                      __typename 
                      ... on DiscountCustomers {
                        customers {
                          id
                          email
                          firstName
                          lastName
                        }
                      }
                  }
                  minimumRequirement {
                      __typename 
                      ... on DiscountMinimumQuantity {
                        greaterThanOrEqualToQuantity
                      }
                      ... on DiscountMinimumSubtotal {
                        greaterThanOrEqualToSubtotal {
                          amount
                          currencyCode
                        }
                      }
                  }
                }
              }
            }
            userErrors {
              field
              code
              message
            }
          }
        }
        """

    variables = {
        "id": f"gid://shopify/DiscountCodeNode/{shopify_discount_code_id}",
        "basicCodeDiscount": {
            "combinesWith": {"orderDiscounts": True, "productDiscounts": True, "shippingDiscounts": False},
            "customerGets": {"items": {"all": True}},
        },
    }

    if discount_fixed_amount:
        variables["basicCodeDiscount"]["customerGets"]["value"] = {
            "discountAmount": {"amount": str(discount_fixed_amount)}
        }

    if discount_percentage:
        variables["basicCodeDiscount"]["customerGets"]["value"] = {"percentage": discount_percentage}

    if minimum_required_amount:
        variables["basicCodeDiscount"]["minimumRequirement"] = {
            "subtotal": {"greaterThanOrEqualToSubtotal": str(minimum_required_amount)}
        }

    status, body = shopify_admin_request({"query": mutation, "variables": variables})

    if status >= 400:
        raise Exception(f"Failed to update discount code in shopify store. Status code: {status}")

    if "errors" in body:
        raise Exception(f"Failed to update discount code in shopify store: {body['errors']}")

    return body.get("data", {}).get("discountCodeBasicUpdate", {}).get("codeDiscountNode", {}).get("codeDiscount")


def main():
    discounts = get_all_not_used_discounts()

    for discount in discounts:
        if not discount.shopify_discount_code or not discount.shopify_discount_code_id:
            continue

        logger.info(f"Processing '{discount.shopify_discount_code}' ======================:")

        if discount.used:
            logger.info(f"Discount '{discount.shopify_discount_code}' was already used. Skipping ...")
            continue

        shopify_discount = get_shopify_discount_by_id(discount.shopify_discount_code_id)

        if not shopify_discount:
            logger.info(f"Discount '{discount.shopify_discount_code}' was not found in Shopify. Skipping ...")
            continue

        logger.info(f"Original discount: {json.dumps(shopify_discount)}")

        if shopify_discount.get("discountClass") == "ORDER":
            title = shopify_discount.get("title")

            if title.startswith("TMG-GROUP-50-OFF-"):
                updated_discount = update_shopify_discount(
                    discount.shopify_discount_code_id, minimum_required_amount=260, discount_fixed_amount=50
                )
            elif title.startswith("TMG-GROUP-25%-OFF-"):
                updated_discount = update_shopify_discount(
                    discount.shopify_discount_code_id, minimum_required_amount=300, discount_percentage=0.25
                )
            elif title.startswith("GIFT-"):
                updated_discount = update_shopify_discount(
                    discount.shopify_discount_code_id,
                    minimum_required_amount=260,
                    discount_fixed_amount=discount.amount,
                )
            else:
                logger.warning(f"Unknown order discount code {title}. Skipping ...")
                continue

            logger.info(f"Updated discount: {json.dumps(updated_discount)}")
        elif shopify_discount.get("discountClass") == "PRODUCT":
            title = shopify_discount.get("title")

            if title.startswith("TMG-GROUP-50-OFF-"):
                updated_discount = update_shopify_discount(
                    discount.shopify_discount_code_id, minimum_required_amount=260, discount_fixed_amount=50
                )
            elif title.startswith("TMG-GROUP-25%-OFF-"):
                updated_discount = update_shopify_discount(
                    discount.shopify_discount_code_id, minimum_required_amount=300, discount_percentage=0.25
                )
            elif title.startswith("GIFT-"):
                updated_discount = update_shopify_discount(
                    discount.shopify_discount_code_id,
                    minimum_required_amount=260,
                    discount_fixed_amount=discount.amount,
                )
            else:
                logger.warning(f"Unknown order discount code {title}. Skipping ...")
                continue

            logger.info(f"Updated discount: {json.dumps(updated_discount)}")
        else:
            raise Exception(f"Unknown discount class: {shopify_discount.get('discountClass')}")


if __name__ == "__main__":
    main()
