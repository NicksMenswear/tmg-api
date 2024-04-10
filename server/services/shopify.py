import os

import requests


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
        created_customer = self.__admin_api_request(
            f"{self.__shopify_admin_api_endpoint}/customers.json",
            {"customer": {"first_name": first_name, "last_name": last_name, "email": email}},
        )

        return created_customer.get("customer")
