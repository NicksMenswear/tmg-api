import os
import random
import json

from server.controllers.util import http

from server.services import ServiceError, NotFoundError, DuplicateError


class FakeShopifyService:
    def create_customer(self, first_name, last_name, email):
        return {"id": random.randint(1000, 100000), "first_name": first_name, "last_name": last_name, "email": email}

    def get_product_by_id(self, product_id):
        return {
            "product_id": product_id,
            "title": "Test Product",
            "vendor": "Test Vendor",
            "body_html": "Test Product Description",
            "images": [{"src": "https://via.placeholder.com/150"}],
            "specific_variant": {
                "id": product_id,
                "title": "Test Product Variant",
                "price": "10.00",
                "inventory_quantity": 10,
            },
        }


class ShopifyService:
    def __init__(self):
        self.__shopify_store = os.getenv("shopify_store")
        self.__admin_api_access_token = os.getenv("admin_api_access_token")
        self.__shopify_admin_api_endpoint = f"https://{self.__shopify_store}.myshopify.com/admin/api/2024-01"

    def admin_api_request(self, method, endpoint, body=None):
        response = http(
            method,
            endpoint,
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.__admin_api_access_token,
            },
        )
        return response.status, json.loads(response.data.decode("utf-8"))

    def create_customer(self, first_name, last_name, email):
        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_admin_api_endpoint}/customers.json",
            {"customer": {"first_name": first_name, "last_name": last_name, "email": email}},
        )
        if status == 422:
            raise DuplicateError("Shopify customer with this email address already exists.")
        if status >= 400:
            raise ServiceError("Failed to create shopify customer.")

        return body["customer"]

    def get_product_by_id(self, product_id):
        status, body = self.admin_api_request("GET", f"{self.__shopify_admin_api_endpoint}/products/{product_id}.json")

        if status == 404:
            raise NotFoundError("Product not found in shopify store.")
        if status >= 400:
            raise ServiceError("Failed to get product from shopify store.")

        product = body["product"]
        product_id = product["id"]
        title = product.get("title")
        vendor = product.get("vendor")
        body_html = product.get("body_html")
        images = product.get("images")
        variants = product.get("variants", [])
        specific_variants = [variant for variant in variants if str(variant["id"]) == str(product.variation_id)]
        specific_variant = specific_variants[0] if len(specific_variants) > 0 else None

        return {
            "product_id": product_id,
            "title": title,
            "vendor": vendor,
            "body_html": body_html,
            "images": images,
            "specific_variant": specific_variant,
        }
