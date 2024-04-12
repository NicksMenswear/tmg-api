import os
import random

import requests

from server.services import ServiceError


class FakeShopifyService:
    def create_customer(self, first_name, last_name, email):
        return {"id": random.randint(1000, 100000), "first_name": first_name, "last_name": last_name, "email": email}


class ShopifyService:
    def __init__(self):
        self.__shopify_store = os.getenv("shopify_store")
        self.__admin_api_access_token = os.getenv("admin_api_access_token")
        self.__shopify_admin_api_endpoint = f"https://{self.__shopify_store}.myshopify.com/admin/api/2024-01"

    def __admin_api_request(self, endpoint, payload):
        response = requests.post(
            endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.__admin_api_access_token,
            },
        )

        return response.json()

    def create_customer(self, first_name, last_name, email):
        try:
            created_customer = self.__admin_api_request(
                f"{self.__shopify_admin_api_endpoint}/customers.json",
                {"customer": {"first_name": first_name, "last_name": last_name, "email": email}},
            )

            return created_customer.get("customer")
        except Exception as e:
            raise ServiceError("Failed to create shopify customer.", e)
