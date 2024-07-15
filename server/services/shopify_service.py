import json
import logging
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any

from server.controllers.util import http
from server.flask_app import FlaskApp
from server.models.shopify_model import ShopifyVariantModel
from server.services import ServiceError, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)


class AbstractShopifyService(ABC):
    @abstractmethod
    def get_online_store_sales_channel_id(self) -> str:
        pass

    @abstractmethod
    def get_online_store_shop_id(self) -> str:
        return "0"

    @abstractmethod
    def get_customer_by_email(self, email: str) -> dict:
        return {}

    @abstractmethod
    def create_customer(self, first_name, last_name, email):
        pass

    @abstractmethod
    def get_account_login_url(self, customer_id):
        pass

    @abstractmethod
    def get_account_activation_url(self, customer_id):
        pass

    @abstractmethod
    def get_variants_by_id(self, variant_ids: List[str]) -> List[ShopifyVariantModel]:
        pass

    @abstractmethod
    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        pass

    @abstractmethod
    def create_virtual_product(self, title, body_html, price, sku, tags, vendor="The Modern Groom"):
        pass

    @abstractmethod
    def delete_product(self, product_id):
        pass

    @abstractmethod
    def get_variant_prices(self, variant_ids: List[str]) -> Dict[str, float]:
        pass

    @abstractmethod
    def create_discount_code(self, title, code, shopify_customer_id, amount, variant_ids):
        pass

    @abstractmethod
    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        pass

    @abstractmethod
    def archive_product(self, shopify_product_id):
        pass

    @abstractmethod
    def create_bundle(self, variant_ids: List[str], image_src: str = None) -> str:
        pass

    @abstractmethod
    def add_image_to_product(self, product_id: str, image_url: str):
        pass


class FakeShopifyService(AbstractShopifyService):
    def __init__(self, shopify_virtual_products=None, shopify_virtual_product_variants=None, shopify_variants=None):
        self.shopify_variants = shopify_variants if shopify_variants else {}
        self.shopify_virtual_products = shopify_virtual_products if shopify_virtual_products else {}
        self.shopify_virtual_product_variants = (
            shopify_virtual_product_variants if shopify_virtual_product_variants else {}
        )
        self.customers = {}

    def get_online_store_sales_channel_id(self) -> str:
        return "gid://shopify/Publication/1234567890"

    def get_online_store_shop_id(self) -> str:
        return "666"

    def get_customer_by_email(self, email: str) -> dict:
        if email.endswith("@shopify-user-does-not-exists.com"):
            raise NotFoundError("Shopify customer doesn't exist.")

        return self.customers.get(email, {"id": random.randint(1000, 100000)})

    def create_customer(self, first_name, last_name, email):
        if email.endswith("@shopify-user-exists.com"):
            raise DuplicateError("Shopify customer with this email address already exists.")

        return {"id": random.randint(1000, 100000), "first_name": first_name, "last_name": last_name, "email": email}

    def get_account_login_url(self, customer_id):
        pass

    def get_account_activation_url(self, customer_id):
        pass

    def create_virtual_product(self, title, body_html, price, sku, tags, vendor="The Modern Groom"):
        virtual_product_id = random.randint(1000, 100000)
        virtual_product_variant_id = random.randint(1000, 100000)
        virtual_product_variant = {"id": virtual_product_variant_id, "title": title, "price": price, "sku": sku}

        virtual_product = {
            "id": virtual_product_id,
            "title": title,
            "vendor": vendor,
            "body_html": body_html,
            "images": [{"src": "https://via.placeholder.com/150"}],
            "variants": [virtual_product_variant],
        }

        self.shopify_virtual_products[virtual_product_id] = virtual_product
        self.shopify_virtual_product_variants[virtual_product_variant_id] = virtual_product_variant

        return virtual_product

    def get_variants_by_id(self, variant_ids: List[str]) -> List[ShopifyVariantModel]:
        return [self.shopify_variants.get(variant_id) for variant_id in variant_ids]

    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        return self.shopify_variants[random.choice(list(self.shopify_variants.keys()))]

    def get_variant_prices(self, variant_ids: List[str]) -> Dict[str, float]:
        result = {}

        for variant_id in variant_ids:
            result[variant_id] = self.shopify_variants.get(variant_id).variant_price

        return result

    def delete_product(self, product_id):
        pass

    def create_discount_code(self, title, code, shopify_customer_id, amount, variant_ids):
        return {
            "shopify_discount_code": code,
            "shopify_discount_id": random.randint(1000, 100000),
        }

    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        pass

    def archive_product(self, shopify_product_id):
        pass

    def create_bundle(self, variant_ids: List[str], image_src: str = None) -> str:
        if not variant_ids:
            raise ServiceError("No variants provided for bundle creation.")

        bundle_price = 0.0

        for variant_id in variant_ids:
            variant = self.shopify_variants.get(variant_id)
            if not variant:
                raise NotFoundError(f"Variant with id {variant_id} not found.")

            bundle_price += variant.variant_price

        bundle_variant_id = str(random.randint(1000000, 1000000000))

        bundle_model = ShopifyVariantModel(
            **{
                "product_id": str(random.randint(10000, 1000000)),
                "product_title": f"Product for bundle {bundle_variant_id}",
                "variant_id": bundle_variant_id,
                "variant_title": f"Variant for bundle {bundle_variant_id}",
                "variant_sku": f"00{random.randint(10000, 1000000)}",
                "variant_price": bundle_price,
            }
        )

        self.shopify_variants[bundle_variant_id] = bundle_model

        return bundle_model.variant_id

    def add_image_to_product(self, product_id: str, image_url: str):
        pass


class ShopifyService(AbstractShopifyService):
    def __init__(self):
        self.__shopify_store = os.getenv("shopify_store")
        self.__shopify_store_host = f"{self.__shopify_store}.myshopify.com"
        self.__admin_api_access_token = os.getenv("admin_api_access_token")
        self.__storefront_api_access_token = os.getenv("storefront_api_access_token")
        self.__shopify_rest_admin_api_endpoint = f"https://{self.__shopify_store_host}/admin/api/2024-01"
        self.__shopify_graphql_admin_api_endpoint = f"https://{self.__shopify_store_host}/admin/api/2024-01"
        self.__shopify_storefront_api_endpoint = f"https://{self.__shopify_store_host}/api/2024-01"

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
        if response.status == 429:
            raise ServiceError(
                f"Shopify API rate limit exceeded. Retry in f{response.headers.get('Retry-After')} seconds."
            )
        if response.status >= 500:
            raise ServiceError(
                f"Shopify API error. Status code: {response.status}, message: {response.data.decode('utf-8')}"
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
        if response.status >= 500:
            raise ServiceError(
                f"Shopify API error. Status code: {response.status}, message: {response.data.decode('utf-8')}"
            )

        return response.status, json.loads(response.data.decode("utf-8"))

    def get_online_store_sales_channel_id(self) -> str:
        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": "{ publications(first: 10) { edges { node { id name } } } }"},
        )

        if status >= 400:
            raise ServiceError(f"Failed to get sales channels in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to get sales channels in shopify store: {body['errors']}")

        publication_edges = body.get("data", {}).get("publications", {}).get("edges", [])

        for publication in publication_edges:
            if publication["node"]["name"] == "Online Store":
                return publication["node"]["id"]

        raise ServiceError("Online Store sales channel not found.")

    def get_online_store_shop_id(self) -> str:
        status, body = self.admin_api_request(
            "POST", f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json", {"query": "{ shop { id } }"}
        )

        if status >= 400:
            raise ServiceError(f"Failed to get shop id. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to get shop id: {body['errors']}")

        shop_id = body.get("data", {}).get("shop", {}).get("id")

        if shop_id and shop_id.startswith("gid://shopify/Shop/"):
            return shop_id.replace("gid://shopify/Shop/", "")

        raise ServiceError("Failed to get shop id.")

    def get_account_login_url(self, customer_id):
        return f"https://{self.__shopify_store_host}/account/login"

    def get_account_activation_url(self, customer_id):
        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_rest_admin_api_endpoint}/customers/{customer_id}/account_activation_url.json",
        )

        if status == 422 and "account already enabled" in body.get("errors", []):
            raise ServiceError("Account already activated.")

        if status >= 400:
            raise ServiceError("Failed to create activation url.")

        return body.get("account_activation_url")

    def get_customer_by_email(self, email: str) -> dict:
        status, body = self.admin_api_request(
            "GET", f"{self.__shopify_rest_admin_api_endpoint}/customers/search.json?query=email:{email}"
        )

        if status >= 400:
            raise ServiceError("Failed to get customer")

        if body.get("customers") and len(body["customers"]) > 0:
            return body["customers"][0]
        else:
            raise NotFoundError("Customer not found.")

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

    def archive_product(self, shopify_product_id):
        status, body = self.admin_api_request(
            "PATCH",
            f"{self.__shopify_rest_admin_api_endpoint}/products/{shopify_product_id}.json",
            {"product": {"id": shopify_product_id, "status": "archived", "published_at": None}},
        )

        if status >= 400:
            raise ServiceError(f"Failed to archive product by id '{shopify_product_id}' in shopify store.")

        if "errors" in body:
            raise ServiceError(
                f"Failed to archive product by id '{shopify_product_id}' in shopify store: {body['errors']}"
            )

        return body.get("product")

    def delete_product(self, shopify_product_id):
        status, body = self.admin_api_request(
            "DELETE", f"{self.__shopify_rest_admin_api_endpoint}/products/{shopify_product_id}.json"
        )

        if status >= 400:
            raise ServiceError(f"Failed to delete product by id '{shopify_product_id}' in shopify store.")

    def create_discount_code(self, title, code, shopify_customer_id, amount, variant_ids):
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
                    "value": {"discountAmount": {"amount": amount, "appliesOnEachItem": False}},
                },
            }
        }

        if variant_ids:
            variables["basicCodeDiscount"]["customerGets"]["items"] = {
                "products": {
                    "productVariantsToAdd": [f"gid://shopify/ProductVariant/{variant_id}" for variant_id in variant_ids]
                }
            }
        else:
            variables["basicCodeDiscount"]["customerGets"]["items"] = {"all": True}

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
            "shopify_discount_code": shopify_discount_code,
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

    def get_variant_prices(self, variant_ids: List[str]) -> Dict[str, float]:
        if not variant_ids:
            return {}

        ids_query = ", ".join(
            [f'"gid://shopify/ProductVariant/{variant_id}"' for variant_id in variant_ids if variant_id]
        )

        query = f"""
        {{
          nodes(ids: [{ids_query}]) {{
            ... on ProductVariant {{
              id
              price
            }}
          }}
        }}
        """

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query},
        )

        if status >= 400:
            raise ServiceError(f"Failed to get prices for {variant_ids} in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to get prices for {variant_ids} in shopify store. {body['errors']}")

        variants_with_prices = {}

        for variant in body["data"]["nodes"]:
            if not variant or "id" not in variant or "price" not in variant:
                continue

            variants_with_prices[variant["id"].removeprefix("gid://shopify/ProductVariant/")] = float(variant["price"])

        return variants_with_prices

    def get_variants_by_id(self, variant_ids: List[str]) -> List[ShopifyVariantModel]:
        if not variant_ids:
            return []

        ids_query = ", ".join(
            [f'"gid://shopify/ProductVariant/{variant_id}"' for variant_id in variant_ids if variant_id]
        )

        query = f"""
        {{
            nodes(ids: [{ids_query}]) {{
            ... on ProductVariant {{
                id
                title
                sku
                price
                product {{
                    id
                    title
                }}
            }}
            }}
        }}
        """

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query},
        )

        if status >= 400:
            raise ServiceError(f"Failed to get titles for {variant_ids} in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to get titles for {variant_ids} in shopify store. {body['errors']}")

        variants = []

        for variant in body["data"]["nodes"]:
            if not variant or "id" not in variant or "title" not in variant or "product" not in variant:
                continue

            product = variant["product"]
            variants.append(
                ShopifyVariantModel(
                    **{
                        "product_id": product["id"].removeprefix("gid://shopify/Product/"),
                        "product_title": product["title"],
                        "variant_id": variant["id"].removeprefix("gid://shopify/ProductVariant/"),
                        "variant_title": variant["title"],
                        "variant_sku": variant["sku"],
                        "variant_price": variant["price"],
                    }
                )
            )

        return variants

    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        query = f"""
        {{
          productVariants(first: 1, query: "sku:{sku}") {{
            edges {{
              node {{
                id
                title
                sku
                product {{
                  id
                  title
                }}
              }}
            }}
          }}
        }}
        """

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query},
        )

        if status >= 400:
            raise ServiceError(f"Failed to get variants by sku in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to get variants by sku in shopify store. {body['errors']}")

        edges = body.get("data", {}).get("productVariants", {}).get("edges")

        if not edges:
            return None

        variant = edges[0].get("node")
        product = variant["product"]

        return ShopifyVariantModel(
            **{
                "product_id": product["id"].removeprefix("gid://shopify/Product/"),
                "product_title": product["title"],
                "variant_id": variant["id"].removeprefix("gid://shopify/ProductVariant/"),
                "variant_title": variant["title"],
                "variant_sku": variant["sku"],
            }
        )

    def add_image_to_product(self, product_id: str, image_url: str):
        mutation = """
        mutation productCreateMedia($media: [CreateMediaInput!]!, $productId: ID!) {
            productCreateMedia(media: $media, productId: $productId) {
                media {
                    alt
                    mediaContentType
                    status
                    ... on MediaImage {
                        id
                        image {
                            originalSrc
                            transformedSrc
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "media": [{"originalSource": image_url, "mediaContentType": "IMAGE", "alt": "Product image"}],
            "productId": product_id,
        }

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to add image to product in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to add image to product in shopify store. {body['errors']}")

        return body

    def create_bundle(self, variant_ids: List[str], image_src: str = None) -> str:
        bundle_parent_product_suffix = random.randint(1000000, 100000000)
        bundle_parent_product_name = f"Suit Bundle #{bundle_parent_product_suffix}"
        bundle_parent_product_handle = f"suit-bundle-{bundle_parent_product_suffix}"
        bundle_parent_product = self.__create_bundle_product(bundle_parent_product_name)

        parent_product_id = bundle_parent_product.get("id")
        parent_product_variant_id = bundle_parent_product.get("variants", {}).get("edges")[0].get("node").get("id")

        shopify_variant_ids = [f"gid://shopify/ProductVariant/{variant_id}" for variant_id in variant_ids if variant_id]

        self.__add_variants_to_product_bundle(parent_product_variant_id, shopify_variant_ids)

        self.__publish_and_add_to_online_sales_channel(
            bundle_parent_product_handle, parent_product_id, FlaskApp.current().online_store_sales_channel_id
        )

        if image_src:
            self.add_image_to_product(parent_product_id, image_src)

        return parent_product_variant_id.removeprefix("gid://shopify/ProductVariant/")

    def __create_bundle_product(self, product_name: str):
        mutation = """
        mutation CreateProductBundle($input: ProductInput!) {
          productCreate(input: $input) {
            product {
              id
              title
              variants(first: 10) {
                edges{
                  node{
                    id
                    price
                  }
                }
              }
            }
            userErrors{
              field
              message
            }
          }
        }
        """
        variables = {"input": {"title": product_name, "variants": []}}

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product bundle in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product bundle in shopify store. {body['errors']}")

        parent_product = body.get("data", {}).get("productCreate", {}).get("product")

        return parent_product

    def __add_variants_to_product_bundle(self, parent_product_shopify_variant_id: str, variants: List[str]):
        bundle_variants = [{"id": variant, "quantity": 1} for variant in variants]

        mutation = """
        mutation CreateBundleComponents($input: [ProductVariantRelationshipUpdateInput!]!) {
          productVariantRelationshipBulkUpdate(input: $input) {
            parentProductVariants {
              id
              productVariantComponents(first: 10) {
                nodes{
                  id
                  quantity
                  productVariant {
                    id
                  }
                }
              }
            }
            userErrors {
              code
              field
              message
            }
          }
        }
        """
        variables = {
            "input": [
                {
                    "parentProductVariantId": parent_product_shopify_variant_id,
                    "productVariantRelationshipsToCreate": bundle_variants,
                }
            ]
        }

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product bundle in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product bundle in shopify store. {body['errors']}")

        return body

    def __publish_and_add_to_online_sales_channel(
        self, product_handle: str, parent_product_id: str, sales_channel_id: str
    ):
        mutation = """
        mutation productUpdate($input: ProductInput!) {
            productUpdate(input: $input) {
                product {
                    id
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """

        variables = {
            "input": {
                "id": parent_product_id,
                "publishedAt": datetime.now(timezone.utc).isoformat(),
                "handle": product_handle,
                "productPublications": {
                    "publicationId": sales_channel_id,
                    "publishDate": datetime.now(timezone.utc).isoformat(),
                },
            },
        }

        status, body = self.admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product bundle in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product bundle in shopify store. {body['errors']}")

        return body
