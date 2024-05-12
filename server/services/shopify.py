import json
import os
import random
from datetime import datetime, timezone

from server.controllers.util import http
from server.database.models import User
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

    def create_virtual_product(self, title, body_html, price, sku, tags, vendor="The Modern Groom"):
        return {
            "id": random.randint(1000, 100000),
            "title": title,
            "vendor": vendor,
            "body_html": body_html,
            "images": [{"src": "https://via.placeholder.com/150"}],
            "variants": [{"id": random.randint(1000, 100000), "title": title, "price": price, "sku": sku}],
        }

    def delete_product(self, product_id):
        pass


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

    def create_virtual_product(self, title, body_html, price, sku, tags, vendor="The Modern Groom"):
        try:
            created_product = self.admin_api_request(
                f"{self.__shopify_admin_api_endpoint}/products.json",
                {
                    "product": {
                        "title": title,
                        "body_html": body_html,
                        "vendor": vendor,
                        "product_type": "Virtual Goods",
                        "tags": tags,
                        # "published_at": None,  # Unpublish from storefront
                        "variants": [
                            {
                                "option1": title,
                                "price": str(price),
                                "sku": sku,
                                "requires_shipping": False,
                                "taxable": False,
                                "inventory_management": None,
                            }
                        ],
                    }
                },
            )

            return created_product.get("product")
        except Exception as e:
            raise ServiceError("Failed to create shopify customer.", e)

    def delete_product(self, product_id):
        try:
            self.admin_api_request(f"{self.__shopify_admin_api_endpoint}/products/{product_id}.json", {}, "DELETE")
        except Exception as e:
            raise ServiceError("Failed to delete product from shopify.", e)

    def create_discount_code(self, groom_user: User, shopify_customer_id: int, amount: int):
        try:
            created_price_rule = self.admin_api_request(
                f"{self.__shopify_admin_api_endpoint}/price_rules.json",
                {
                    "price_rule": {
                        "title": f"Groom {groom_user.first_name} discount gift",
                        "target_type": "line_item",
                        "target_selection": "all",
                        "allocation_method": "across",
                        "value_type": "fixed_amount",
                        "value": f"-{str(int(amount))}.00",
                        "customer_selection": "prerequisite",
                        "prerequisite_customer_ids": [shopify_customer_id],
                        "once_per_customer": True,
                        "combine_with": "combine_with_all",
                        "usage_limit": 1,
                        "starts_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )

            created_price_rule = created_price_rule.get("price_rule")

            price_rule_id = created_price_rule["id"]

            created_discount_code = self.admin_api_request(
                f"{self.__shopify_admin_api_endpoint}/price_rules/{price_rule_id}/discount_codes.json",
                {
                    "discount_code": {
                        "code": f"GROOM-{groom_user.first_name.upper()}-GIFT-{amount}-OFF-{random.randint(100000, 999999)}"
                    }
                },
            )

            created_discount_code = created_discount_code.get("discount_code")
        except Exception as e:
            raise ServiceError("Failed to create shopify customer.", e)

        return {
            "shopify_discount_id": created_discount_code["id"],
            "code": created_discount_code["code"],
        }
