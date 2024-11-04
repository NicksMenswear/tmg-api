import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.controllers.util import http
from server.database.models import SuitBuilderItem

DB_HOST = "tmg-db-stg-02.cfbqizbq9cdk.us-west-2.rds.amazonaws.com"
DB_NAME = "tmg"
DB_USER = "postgres"
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")
SHOPIFY_STORE_HOST = os.getenv("SHOPIFY_STORE_HOST", "tmg-staging")
SHOPIFY_STORE_ADMIN_GRAPHQL_ENDPOINT = f"https://{SHOPIFY_STORE_HOST}.myshopify.com/admin/api/2024-01/graphql.json"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()


def get_suit_builder_items():
    return session.query(SuitBuilderItem).all()


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


def get_shopify_item_by_sku(sku):
    print("Getting shopify item by sku:", sku)

    query = f"""
    {{
      productVariants(first: 1, query: "sku:{sku}") {{
        edges {{
          node {{
            id
            product {{
              id
            }}
          }}
        }}
      }}
    }}
    """

    status, body = shopify_admin_request(
        {"query": query},
    )

    if status >= 400:
        raise Exception(f"Failed to get variants by sku in shopify store. Status code: {status}")

    if "errors" in body:
        raise Exception(f"Failed to get variants by sku in shopify store. {body['errors']}")

    edges = body.get("data", {}).get("productVariants", {}).get("edges")

    if not edges:
        return None

    variant = edges[0].get("node")
    product = variant["product"]

    return {
        "product_id": int(product["id"].removeprefix("gid://shopify/Product/")),
        "variant_id": int(variant["id"].removeprefix("gid://shopify/ProductVariant/")),
    }


def main():
    items = get_suit_builder_items()

    for item in items:
        sku = item.sku

        if not sku:
            continue

        shopify_item = get_shopify_item_by_sku(sku)

        if not shopify_item:
            continue

        item_variant_id = shopify_item.get("variant_id")
        item_product_id = shopify_item.get("product_id")

        if not item_variant_id or not item_product_id:
            continue

        item.variant_id = item_variant_id
        item.product_id = item_product_id

        session.commit()


if __name__ == "__main__":
    main()
