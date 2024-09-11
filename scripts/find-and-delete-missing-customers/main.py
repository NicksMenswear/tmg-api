import json
import logging
import os
from typing import List, Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.controllers.util import http
from server.database.models import Discount, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "tmg-db-dev-01.cfbqizbq9cdk.us-west-2.rds.amazonaws.com")
DB_NAME = os.getenv("DB_NAME", "tmg")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_URI = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "customers_export.csv")
SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")
SHOPIFY_STORE_HOST = os.getenv("SHOPIFY_STORE_HOST", "quickstart-a91e1214.myshopify.com")
SHOPIFY_STORE_ADMIN_GRAPHQL_ENDPOINT = f"https://{SHOPIFY_STORE_HOST}/admin/api/2024-01/graphql.json"

db_engine = create_engine(DB_URI)
Session = sessionmaker(bind=db_engine)
session = Session()


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


def read_customers_from_csv_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as file:
        lines = file.readlines()

    customers = {}

    for line in lines[1:]:
        line = line.strip()
        parts = line.split(",")

        shopify_id = parts[0]
        first_name = parts[1]
        last_name = parts[2]
        email = parts[3]
        total_orders = parts[16]

        if not email:
            continue

        customers[email.lower()] = {
            "id": shopify_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "total_orders": total_orders,
        }

    return customers


def get_all_customer_from_db() -> Dict[str, Any]:
    customers = session.query(User).all()

    db_customers = {}

    for customer in customers:
        if not customer.email:
            continue

        db_customers[customer.email.lower()] = {
            "id": customer.shopify_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
        }

    return db_customers


def delete_shopify_customer(shopify_customer_id: int) -> None:
    mutation = """
        mutation customerDelete($id: ID!) {
          customerDelete(input: {id: $id}) {
            shop {
              id
            }
            userErrors {
              field
              message
            }
            deletedCustomerId
          }
        }
        """

    variables = {"id": f"gid://shopify/Customer/{shopify_customer_id}"}

    status, body = shopify_admin_request({"query": mutation, "variables": variables})

    if status >= 400:
        raise Exception(f"Failed to delete customer in shopify store: {body}")

    if "errors" in body:
        return


def main():
    shopify_customers = read_customers_from_csv_file(CSV_FILE_PATH)
    db_customers = get_all_customer_from_db()

    missing_customers = {}
    for email, customer in shopify_customers.items():
        if email in db_customers:
            continue

        missing_customers[email] = customer

        logger.info(f"Missing customer: {json.dumps(customer)}")

        delete_shopify_customer(int(customer["id"]))


if __name__ == "__main__":
    main()
