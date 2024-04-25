import json
import logging
import os

import urllib3

from server.controllers.util import http
from server.database.database_manager import db
from server.database.models import User

logger = logging.getLogger(__name__)


shopify_store = os.getenv("shopify_store")
client_id = os.getenv("client_id")
admin_api_access_token = os.getenv("admin_api_access_token")
client_secret = os.getenv("client_secret")
api_version = os.getenv("api_version")


def search_customer_by_email(email):
    try:

        user = db.session.query(User).filter(User.email == email).first()
        response = http(
            "GET",
            f"https://{shopify_store}.myshopify.com/admin/api/2024-01/customers/{user.shopify_id}.json",
            headers={
                "X-Shopify-Access-Token": admin_api_access_token,
            },
        )
        response.raise_for_status()
        customers = json.loads(response.data.decode("utf-8")).get("customers", [])
        return customers
    except urllib3.exceptions.RequestError as error:
        logger.error("Error searching for customer by email:", error)
        raise


def create_shopify_customer(customer_data):
    response = http(
        "POST",
        f"https://{shopify_store}.myshopify.com/admin/api/2024-01/customers.json",
        json={"customer": customer_data},
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": admin_api_access_token,
        },
    )
    created_customer = json.loads(response.data.decode("utf-8")).get("customer", {})
    return created_customer


def get_access_token():
    try:
        response = http(
            "POST",
            f"https://{shopify_store}.myshopify.com/admin/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        access_token = response.json().get("access_token")
        return access_token
    except urllib3.exceptions.RequestError as error:
        logger.error("Error searching for customer by email:", error)
        raise


def get_customer(email):
    try:
        customers = search_customer_by_email(email)
        return customers
    except Exception as e:
        logger.error(f"An error occurred: {e}")


# TODO delete this function
def list_customer():
    customer_email = "syed@nicksmenswear.com"
    try:
        customers = search_customer_by_email(customer_email)
        logger.info("Found customers: ", customers)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


def get_activation_url(customer_id):
    try:
        url = f"https://{shopify_store}.myshopify.com/admin/api/{api_version}/customers/{customer_id}/account_activation_url.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": admin_api_access_token,
        }
        response = http("POST", url, headers=headers)
        if response.status == 200:
            activation_url = json.loads(response.data.decode("utf-8")).get("account_activation_url")
            logger.info(f"Activation URL: {activation_url}")
            return activation_url
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


def create_customer(customer_data):
    created_customer = create_shopify_customer(customer_data)
    if created_customer:
        logger.info("Created customer:", created_customer["id"])
        return created_customer["id"]
