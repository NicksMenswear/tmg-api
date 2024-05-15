import json
import logging
import os

from server.controllers.util import http

logger = logging.getLogger(__name__)


shopify_store = os.getenv("shopify_store")
client_id = os.getenv("client_id")
admin_api_access_token = os.getenv("admin_api_access_token")
client_secret = os.getenv("client_secret")
api_version = os.getenv("api_version")


def get_activation_url(customer_id):
    try:
        url = f"https://{shopify_store}.myshopify.com/admin/api/{api_version}/customers/{customer_id}/account_activation_url.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": admin_api_access_token,
        }
        response = http("POST", url, headers=headers)
        if response.status >= 400:
            return f"Failed to create account_activation_url {response.status}", 500

        activation_url = json.loads(response.data.decode("utf-8")).get("account_activation_url")
        logger.info(f"Activation URL: {activation_url}")

        return activation_url
    except Exception as e:
        logger.exception(e)
        return f"Internal Server Error : {e}", 500
