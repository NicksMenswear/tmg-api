import json
import logging
import os
import random
from datetime import datetime, timezone

from server.controllers.util import http
from server.services import ServiceError, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)


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
        self.__storefront_api_access_token = os.getenv("storefront_api_access_token")
        self.__shopify_rest_admin_api_endpoint = f"https://{self.__shopify_store}.myshopify.com/admin/api/2024-01"
        self.__shopify_graphql_admin_api_endpoint = f"https://{self.__shopify_store}.myshopify.com/admin/api/2024-01"
        self.__shopify_storefront_api_endpoint = f"https://{self.__shopify_store}.myshopify.com/api/2024-01"

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

    def storefront_api_request(self, method, endpoint, body=None):
        response = http(
            method,
            endpoint,
            json=body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Storefront-Access-Token": self.__storefront_api_access_token,
            },
        )

        return response.status, json.loads(response.data.decode("utf-8"))

    def get_activation_url(self, customer_id):
        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_rest_admin_api_endpoint}/customers/{customer_id}/account_activation_url.json",
        )

        if status >= 400:
            raise ServiceError("Failed to create shopify customer.")

        return body.get("account_activation_url")

    def create_customer(self, first_name, last_name, email):
        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_rest_admin_api_endpoint}/customers.json",
            {"customer": {"first_name": first_name, "last_name": last_name, "email": email}},
        )

        if status == 422:
            raise DuplicateError("Shopify customer with this email address already exists.")
        if status >= 400:
            raise ServiceError("Failed to create shopify customer.")

        return body["customer"]

    def get_product_by_id(self, product_id):
        status, body = self.admin_api_request(
            "GET", f"{self.__shopify_rest_admin_api_endpoint}/products/{product_id}.json"
        )

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
        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_rest_admin_api_endpoint}/products.json",
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

        if status >= 400:
            raise ServiceError("Failed to create virtual product in shopify store.")

        return body.get("product")

    def delete_product(self, product_id):
        status, body = self.admin_api_request(
            "DELETE", f"{self.__shopify_rest_admin_api_endpoint}/products/{product_id}.json"
        )

        if status >= 400:
            raise ServiceError(f"Failed to delete product by id '{product_id}' in shopify store.")

    def create_discount_code(self, title, code, shopify_customer_id, amount):
        status, created_price_rule = self.admin_api_request(
            "POST",
            f"{self.__shopify_rest_admin_api_endpoint}/price_rules.json",
            {
                "price_rule": {
                    "title": title,
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

        if status >= 400:
            raise ServiceError(f"Failed to create price rule in shopify store.")

        created_price_rule = created_price_rule.get("price_rule")

        price_rule_id = created_price_rule["id"]

        status, created_discount_code = self.admin_api_request(
            "POST",
            f"{self.__shopify_rest_admin_api_endpoint}/price_rules/{price_rule_id}/discount_codes.json",
            {"discount_code": {"code": code}},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create discount in shopify store.")

        created_discount_code = created_discount_code.get("discount_code")

        return {
            "shopify_discount_id": created_discount_code["id"],
            "code": created_discount_code["code"],
        }

    def create_discount_code2(self, title, code, shopify_customer_id, amount):
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
                  codes(first: 10) {
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

        variables = {
            "basicCodeDiscount": {
                "title": title,
                "code": code,
                "usageLimit": 1,
                "customerSelection": {"customers": {"add": [f"gid://shopify/Customer/{shopify_customer_id}"]}},
                "startsAt": datetime.now(timezone.utc).isoformat(),
                "appliesOncePerCustomer": True,
                "combinesWith": {"orderDiscounts": True, "productDiscounts": True, "shippingDiscounts": True},
                "customerGets": {
                    "items": {"all": True},
                    "value": {"discountAmount": {"amount": amount, "appliesOnEachItem": False}},
                },
            }
        }

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create discount code in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to apply discount codes to cart in shopify store: {body['errors']}")

        logger.info(f"Discount code created: {body}")

        shopify_discount = body["data"]["discountCodeBasicCreate"]["codeDiscountNode"]
        shopify_discount_id = shopify_discount["id"].split("/")[-1]
        shopify_discount_code = shopify_discount["codeDiscount"]["codes"]["nodes"][0]["code"]

        return {
            "shopify_discount_id": shopify_discount_id,
            "code": shopify_discount_code,
        }

    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        status, body = self.storefront_api_request(
            "POST",
            f"{self.__shopify_storefront_api_endpoint}/graphql.json",
            {
                "query": "mutation cartDiscountCodesUpdate($cartId: ID!, $discountCodes: [String!]!) {cartDiscountCodesUpdate(cartId: $cartId, discountCodes: $discountCodes) { cart { id } } }",
                "variables": {"cartId": f"gid://shopify/Cart/{cart_id}", "discountCodes": discount_codes},
            },
        )

        if status >= 400:
            raise ServiceError(f"Failed to apply discount codes to cart in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to apply discount codes to cart in shopify store: {body['errors']}")

        return body
