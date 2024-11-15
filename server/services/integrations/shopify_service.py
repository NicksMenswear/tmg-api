import enum
import fnmatch
import json
import logging
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from server.controllers.util import http
from server.models.shopify_model import ShopifyCustomer, ShopifyVariantModel, ShopifyProduct, ShopifyVariant
from server.services import ServiceError, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)


class DiscountAmountType(enum.Enum):
    FIXED_AMOUNT = "fixed_amount"
    PERCENTAGE = "percentage"


class ShopifyQueryError(Exception):
    def __init__(self):
        super().__init__("Shopify API Error")


class AbstractShopifyService(ABC):
    @abstractmethod
    def get_account_login_url(self) -> str:
        pass

    @abstractmethod
    def get_account_activation_url(self, customer_id: int) -> str:
        pass

    @abstractmethod
    def get_customer_by_email(self, email: str) -> ShopifyCustomer | None:
        pass

    @abstractmethod
    def get_customers_by_email_pattern(self, email_pattern: str, num_customers_to_fetch=100) -> list[ShopifyCustomer]:
        pass

    @abstractmethod
    def create_customer(self, first_name: str, last_name: str, email: str) -> ShopifyCustomer:
        pass

    @abstractmethod
    def update_customer(
        self,
        customer_gid: str,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        phone_number: str = None,
        latest_sizing: str = None,
    ) -> ShopifyCustomer:
        pass

    @abstractmethod
    def delete_customer(self, customer_gid: str) -> None:
        pass

    @abstractmethod
    def add_tags(self, shopify_gid: str, tags: set[str]) -> None:
        pass

    @abstractmethod
    def remove_tags(self, shopify_gid: str, tags: set[str]) -> None:
        pass

    @abstractmethod
    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        pass

    @abstractmethod
    def get_variants_by_skus(self, skus: list[str]) -> list[ShopifyVariantModel]:
        pass

    @abstractmethod
    def archive_product(self, product_gid: str) -> None:
        pass

    @abstractmethod
    def delete_product(self, product_gid: str) -> None:
        pass

    @abstractmethod
    def get_variants_by_id(self, variant_ids: list[str]) -> list[ShopifyVariantModel]:
        pass

    @abstractmethod
    def create_discount_code(
        self,
        title: str,
        code: str,
        shopify_customer_id: str,
        discount_type: DiscountAmountType,
        amount: float,
        minimum_order_amount: int | None = None,
        variant_ids: list[str] | None = None,
    ):
        pass

    @abstractmethod
    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        pass

    @abstractmethod
    def delete_discount(self, discount_code_gid: str) -> None:
        pass

    @abstractmethod
    def create_product(
        self, title: str, body_html: str, price: float, sku: str, tags: list[str], requires_shipping: bool = True
    ) -> ShopifyProduct:
        pass

    @abstractmethod
    def create_attendee_discount_product(
        self, title: str, body_html: str, amount: float, sku: str, tags: list[str]
    ) -> ShopifyProduct:
        pass

    @abstractmethod
    def create_bundle(
        self,
        bundle_name: str,
        bundle_id: str,
        variant_ids: list[str],
        image_src: str = None,
        tags: list[str] = None,
    ) -> str:
        pass

    @abstractmethod
    def create_bundle2(
        self,
        bundle_name: str,
        bundle_id: str,
        variant_ids: list[str],
        image_src: str = None,
        tags: list[str] = None,
    ) -> ShopifyVariantModel:
        pass

    @abstractmethod
    def create_bundle_identifier_product(self, bundle_id: str) -> ShopifyProduct:
        pass

    @abstractmethod
    def deactivate_discount(self, discount_gid: str) -> None:
        pass

    @abstractmethod
    def add_products_to_collection(self, collection_id: int, product_ids: list[int]) -> None:
        pass


class FakeShopifyService(AbstractShopifyService):
    def __init__(self, shopify_virtual_products=None, shopify_virtual_product_variants=None, shopify_variants=None):
        self.shopify_variants = shopify_variants if shopify_variants else {}
        self.shopify_virtual_products = shopify_virtual_products if shopify_virtual_products else {}
        self.shopify_virtual_product_variants = (
            shopify_virtual_product_variants if shopify_virtual_product_variants else {}
        )
        self.customers: dict[str, ShopifyCustomer] = {}

    def get_account_login_url(self) -> str:
        pass

    def get_account_activation_url(self, customer_id: int) -> str:
        pass

    def get_customer_by_email(self, email: str) -> ShopifyCustomer | None:
        if email.endswith("@shopify-user-does-not-exists.com"):
            return None

        for customer in self.customers.values():
            if customer.email == email:
                return customer

        return None

    def get_customers_by_email_pattern(self, email_pattern: str, num_customers_to_fetch=100) -> list[ShopifyCustomer]:
        customers = []

        for gid, customer in self.customers.items():
            if fnmatch.fnmatch(customer.email, email_pattern):
                customers.append(customer)

        return customers[:num_customers_to_fetch]

    def create_customer(self, first_name: str, last_name: str, email: str) -> ShopifyCustomer:
        if email.endswith("@shopify-user-exists.com"):
            raise DuplicateError("Shopify customer with this email address already exists.")

        return ShopifyCustomer(
            gid=ShopifyService.customer_gid(random.randint(1000, 100000)),
            email=email,
            first_name=first_name,
            last_name=last_name,
            state="enabled",
            tags=[],
        )

    def update_customer(
        self,
        customer_gid: str,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        phone_number: str = None,
        latest_sizing: str = None,
    ) -> ShopifyCustomer:
        pass

    def delete_customer(self, customer_gid: str) -> None:
        for email, customer in self.customers.items():
            if customer.gid == customer_gid:
                del self.customers[customer.gid]
                break

    def __get_variant_by_product_id(self, product_id: str) -> ShopifyVariantModel | None:
        for variant in self.shopify_variants.values():
            if variant.product_id == product_id:
                return variant

        return None

    def add_tags(self, shopify_gid: str, tags: set[str]) -> None:
        if not shopify_gid:
            return

        if shopify_gid.startswith("gid://shopify/Customer/"):
            customer = self.customers.get(shopify_gid)

            if not customer:
                raise NotFoundError(f"Customer with id {shopify_gid} not found.")

            customer.tags = list(set(customer.tags) | tags)
        elif shopify_gid.startswith("gid://shopify/Product/"):
            product_id = shopify_gid.removeprefix("gid://shopify/Product/")
            variant = self.__get_variant_by_product_id(product_id)

            if not variant:
                raise NotFoundError(f"Variant with id {shopify_gid} not found.")

            variant.tags = list(set(variant.tags) | tags)

    def remove_tags(self, shopify_gid: str, tags: set[str]) -> None:
        if not shopify_gid:
            return

        if shopify_gid.startswith("gid://shopify/Customer/"):
            customer = self.customers.get(shopify_gid)

            if not customer:
                raise NotFoundError(f"Customer with id {shopify_gid} not found.")

            customer.tags = list(set(customer.tags) - set(tags))
        elif shopify_gid.startswith("gid://shopify/Product/"):
            product_id = shopify_gid.removeprefix("gid://shopify/Product/")
            variant = self.__get_variant_by_product_id(product_id)

            if not variant:
                raise NotFoundError(f"Variant with id {shopify_gid} not found.")

            variant.tags = list(set(variant.tags) - set(tags))

    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        return self.shopify_variants[random.choice(list(self.shopify_variants.keys()))]

    def get_variants_by_skus(self, skus: list[str]) -> list[ShopifyVariantModel]:
        result = []

        for sku in skus:
            result.append(self.get_variant_by_sku(sku))

        return result

    def get_variants_by_id(self, variant_ids: list[str]) -> list[ShopifyVariantModel]:
        return [self.shopify_variants.get(variant_id) for variant_id in variant_ids]

    def archive_product(self, product_gid: str) -> None:
        pass

    def delete_product(self, product_gid: str) -> None:
        pass

    def create_discount_code(
        self,
        title: str,
        code: str,
        shopify_customer_id: str,
        discount_type: DiscountAmountType,
        amount: float,
        minimum_order_amount: int | None = None,
        variant_ids: list[str] | None = None,
    ):
        return {
            "shopify_discount_code": code,
            "shopify_discount_id": random.randint(1000, 100000),
        }

    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        pass

    def delete_discount(self, discount_code_gid: str) -> None:
        pass

    def create_product(
        self, title: str, body_html: str, price: float, sku: str, tags: list[str], requires_shipping: bool = True
    ) -> ShopifyProduct:
        created_product = ShopifyProduct(
            gid=ShopifyService.product_gid(random.randint(1000, 100000)),
            title=title,
            tags=tags,
            variants=[
                ShopifyVariant(
                    gid=ShopifyService.product_variant_gid(random.randint(1000, 100000)),
                    title=title,
                    price=price,
                    sku=sku,
                )
            ],
        )

        self.shopify_virtual_products[created_product.gid] = created_product
        created_product_variant = created_product.variants[0]

        self.shopify_variants[str(created_product_variant.get_id())] = ShopifyVariantModel(
            **{
                "product_id": str(created_product.get_id()),
                "product_title": f"Product for variant {created_product.get_id()}",
                "variant_id": str(created_product_variant.get_id()),
                "variant_title": f"Variant {created_product.get_id()}",
                "variant_sku": created_product_variant.sku,
                "variant_price": created_product_variant.price,
            }
        )
        self.shopify_virtual_product_variants[created_product_variant.get_id()] = {
            "id": str(created_product_variant.get_id()),
            "title": title,
            "price": price,
            "sku": sku,
        }

        return created_product

    def create_attendee_discount_product(
        self, title: str, body_html: str, amount: float, sku: str, tags: list[str]
    ) -> ShopifyProduct:
        return self.create_product(title, body_html, amount, sku, tags, False)

    def create_bundle(
        self,
        bundle_name: str,
        bundle_id: str,
        variant_ids: list[str],
        image_src: str = None,
        tags: list[str] = None,
    ):
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
                "tags": tags,
            }
        )

        self.shopify_variants[bundle_variant_id] = bundle_model

        return bundle_model.variant_id

    def create_bundle2(
        self,
        bundle_name: str,
        bundle_id: str,
        variant_ids: list[str],
        image_src: str = None,
        tags: list[str] = None,
    ) -> ShopifyVariantModel:
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
                "tags": tags,
            }
        )

        self.shopify_variants[bundle_variant_id] = bundle_model

        return bundle_model

    def create_bundle_identifier_product(self, bundle_id: str) -> ShopifyProduct:
        return self.create_product(
            title=f"Bundle #{bundle_id}",
            body_html="",
            price=0.0,
            sku=f"bundle-{bundle_id}",
            tags=[],
        )

    def deactivate_discount(self, discount_gid: str) -> None:
        return

    def add_products_to_collection(self, collection_id: int, product_ids: list[int]) -> None:
        pass


class ShopifyService(AbstractShopifyService):
    def __init__(self, online_store_sales_channel_id: str):
        self.__online_store_sales_channel_id = online_store_sales_channel_id
        self.__shopify_store = os.getenv("shopify_store")
        self.__stage = os.getenv("STAGE", "dev")
        self.__bundle_image_path = f"https://data.{self.__stage}.tmgcorp.net/bundle.jpg"
        self.__gift_image_path = f"https://data.{self.__stage}.tmgcorp.net/giftcard.jpg"
        self.__shopify_store_host = f"{self.__shopify_store}.myshopify.com"
        self.__admin_api_access_token = os.getenv("admin_api_access_token")
        self.__storefront_api_access_token = os.getenv("storefront_api_access_token")
        self.__shopify_graphql_admin_api_endpoint = f"https://{self.__shopify_store_host}/admin/api/2024-01"
        self.__shopify_storefront_api_endpoint = f"https://{self.__shopify_store_host}/api/2024-01"

    @classmethod
    def customer_gid(cls, shopify_id: int) -> str:
        return f"gid://shopify/Customer/{shopify_id}"

    @classmethod
    def product_gid(cls, shopify_id: int) -> str:
        return f"gid://shopify/Product/{shopify_id}"

    @classmethod
    def collection_gid(cls, shopify_id: int) -> str:
        return f"gid://shopify/Collection/{shopify_id}"

    @classmethod
    def discount_gid(cls, shopify_id: int) -> str:
        return f"gid://shopify/DiscountCodeNode/{shopify_id}"

    @classmethod
    def product_variant_gid(cls, shopify_id: int) -> str:
        return f"gid://shopify/ProductVariant/{shopify_id}"

    def get_account_login_url(self) -> str:
        return f"https://{self.__shopify_store_host}/account/login"

    def get_account_activation_url(self, customer_id: int) -> str:
        query = """
        mutation customerGenerateAccountActivationUrl($customerId: ID!) {
          customerGenerateAccountActivationUrl(customerId: $customerId) {
            accountActivationUrl
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {"customerId": ShopifyService.customer_gid(customer_id)}

        try:
            body = self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to create activation url")

        return body.get("data", {}).get("customerGenerateAccountActivationUrl", {}).get("accountActivationUrl")

    def get_customer_by_email(self, email: str) -> ShopifyCustomer | None:
        query = """
        query($query: String!) {
          customers(first: 1, query: $query) {
            edges {
              node {
                id
                email
                firstName
                lastName
                state
                tags
              }
            }
          }
        }
        """

        variables = {"query": f"email:{email}"}

        try:
            body = self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to get customer")

        customers = body.get("data", {}).get("customers", {}).get("edges", [])

        if customers:
            customer = customers[0]["node"]

            return ShopifyCustomer(
                gid=customer["id"],
                email=customer["email"],
                first_name=customer["firstName"],
                last_name=customer["lastName"],
                state=customer["state"].lower(),
                tags=customer["tags"],
            )

        return None

    def get_customers_by_email_pattern(self, email_pattern: str, num_customers_to_fetch=100) -> list[ShopifyCustomer]:
        query = f'{{ customers(first: {num_customers_to_fetch}, query: "email:{email_pattern}") {{ edges {{ node {{ id email firstName lastName state tags }} }} }} }}'

        try:
            body = self.__admin_api_graphql_request(query)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to get customers by email suffix")

        customer_edges = body.get("data", {}).get("customers", {}).get("edges", [])

        customers = []

        for edge in customer_edges:
            customer = edge.get("node")
            customers.append(
                ShopifyCustomer(
                    gid=customer["id"],
                    email=customer["email"],
                    first_name=customer["firstName"],
                    last_name=customer["lastName"],
                    state=customer["state"].lower(),
                    tags=customer["tags"],
                )
            )

        return customers

    def create_customer(self, first_name: str, last_name: str, email: str) -> ShopifyCustomer:
        query = """
        mutation customerCreate($input: CustomerInput!) {
          customerCreate(input: $input) {
            customer {
              id
              email
              firstName
              lastName
              state
              tags
            }
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {"input": {"firstName": first_name, "lastName": last_name, "email": email}}

        try:
            body = self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to create customer")

        customer = body.get("data", {}).get("customerCreate", {}).get("customer")

        return ShopifyCustomer(
            gid=customer["id"],
            email=customer["email"],
            first_name=customer["firstName"],
            last_name=customer["lastName"],
            state=customer["state"].lower(),
            tags=customer["tags"],
        )

    def update_customer(
        self,
        customer_gid: str,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        phone_number: str = None,
        latest_sizing: str = None,
    ) -> ShopifyCustomer:
        query = """
        mutation customerUpdate($input: CustomerInput!) {
          customerUpdate(input: $input) {
            customer {
              id
              firstName
              lastName
              email
              state
              tags
            }
            userErrors {
              field
              message
            }
        }
        }
        """

        customer_input = {"id": customer_gid}

        if first_name:
            customer_input["firstName"] = first_name
        if last_name:
            customer_input["lastName"] = last_name
        if email:
            customer_input["email"] = email
        if phone_number:
            customer_input["phone"] = phone_number
        if latest_sizing:
            customer_input["metafields"] = [
                {"namespace": "custom", "key": "latest_sizing", "value": latest_sizing},
            ]

        variables = {"input": customer_input}

        try:
            body = self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to update shopify customer.")

        user_errors = body.get("data", {}).get("customerUpdate", {}).get("userErrors", [])

        if user_errors:
            logger.error(f"Failed to update Shopify customer: {user_errors}")
            raise ServiceError("Failed to update Shopify customer.")

        customer = body.get("data", {}).get("customerUpdate", {}).get("customer")

        return ShopifyCustomer(
            gid=customer["id"],
            email=customer["email"],
            first_name=customer["firstName"],
            last_name=customer["lastName"],
            state=customer["state"].lower(),
            tags=customer["tags"],
        )

    def delete_customer(self, customer_gid: str) -> None:
        query = """
        mutation customerDelete($input: CustomerDeleteInput!) {
          customerDelete(input: $input) {
            deletedCustomerId
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {"input": {"id": customer_gid}}

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to delete customer")

    def add_tags(self, shopify_gid: str, tags: set[str]) -> None:
        query = """
            mutation addTags($id: ID!, $tags: [String!]!) {
                tagsAdd(id: $id, tags: $tags) {
                    node {
                        id
                    }
                    userErrors {
                        message
                    }
                }
            }
        """

        variables = {
            "id": shopify_gid,
            "tags": ",".join(list(tags)),
        }

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to add tags in shopify store.")

    def remove_tags(self, shopify_gid: str, tags: set[str]) -> None:
        query = """
            mutation removeTags($id: ID!, $tags: [String!]!) {
                tagsRemove(id: $id, tags: $tags) {
                    node {
                        id
                    }
                    userErrors {
                        message
                    }
                }
            }
        """

        variables = {
            "id": shopify_gid,
            "tags": ",".join(list(tags)),
        }

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to remove tags in shopify store.")

    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel | None:
        query = f"""
        {{
          productVariants(first: 1, query: "sku:{sku}") {{
            edges {{
              node {{
                id
                title
                sku
                price
                product {{
                  id
                  title
                  images(first: 1) {{
                    edges {{
                      node {{
                        url
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """

        try:
            body = self.__admin_api_graphql_request(query)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to get variants by sku in shopify store.")

        edges = body.get("data", {}).get("productVariants", {}).get("edges")

        if not edges:
            return None

        variant = edges[0].get("node")
        product = variant["product"]
        image_edges = product.get("images", {}).get("edges", [{}])
        image_url = image_edges[0].get("node", {}).get("url") if image_edges else None

        return ShopifyVariantModel(
            **{
                "product_id": product["id"].removeprefix("gid://shopify/Product/"),
                "product_title": product["title"],
                "variant_id": variant["id"].removeprefix("gid://shopify/ProductVariant/"),
                "variant_title": variant["title"],
                "variant_price": variant["price"],
                "variant_sku": variant["sku"],
                "image_url": image_url,
            }
        )

    def get_variants_by_skus(self, skus: list[str]) -> list[ShopifyVariantModel]:
        if not skus:
            return []

        or_statement = " OR ".join([f"sku:{sku}" for sku in skus])

        query = f"""
        {{
            products(first: 100, query: "{or_statement}") {{
                edges {{
                    node {{
                        id
                        title
                        images(first: 1) {{
                            edges {{
                                node {{
                                    url
                                }}
                            }}
                        }}
                        variants(first: 1) {{
                            edges {{
                                node {{
                                    id
                                    title
                                    sku
                                    price
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """

        try:
            body = self.__admin_api_graphql_request(query)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to get variants by sku in shopify store.")

        edges = body.get("data", {}).get("products", {}).get("edges")

        if not edges:
            return []

        variants: list[ShopifyVariantModel] = []

        for edge in edges:
            product = edge.get("node")
            variant = product.get("variants", {}).get("edges", [{}])[0].get("node")
            image_edges = product.get("images", {}).get("edges", [{}])
            image_url = image_edges[0].get("node", {}).get("url") if image_edges else None

            variants.append(
                ShopifyVariantModel(
                    **{
                        "product_id": product["id"].removeprefix("gid://shopify/Product/"),
                        "product_title": product["title"],
                        "variant_id": variant["id"].removeprefix("gid://shopify/ProductVariant/"),
                        "variant_title": variant["title"],
                        "variant_price": variant["price"],
                        "variant_sku": variant["sku"],
                        "image_url": image_url,
                    }
                )
            )

        return variants

    def get_variants_by_id(self, variant_ids: list[str]) -> list[ShopifyVariantModel]:
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

        try:
            body = self.__admin_api_graphql_request(query)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to get variants by ids in shopify store.")

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

    def archive_product(self, product_gid: str) -> None:
        query = """
        mutation productUpdate($input: ProductInput!) {
          productUpdate(input: $input) {
            product {
              id
              status
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
                "id": product_gid,
                "status": "ARCHIVED",
            }
        }

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to archive product by id '{product_gid}'")

    def delete_product(self, product_gid: str) -> None:
        query = """
        mutation productDelete($id: ID!) {
          productDelete(input: {id: $id}) {
            deletedProductId
            userErrors {
              field
              message
            }
          }
        }
        """

        variables = {"id": product_gid}

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to delete product by id '{product_gid}'")

    def create_discount_code(
        self,
        title: str,
        code: str,
        shopify_customer_id: str,
        discount_type: DiscountAmountType,
        amount: float,
        minimum_order_amount: int | None = None,
        variant_ids: list[str] | None = None,
    ):
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
                  codes(first: 1) {
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
                "customerSelection": {"customers": {"add": [ShopifyService.customer_gid(int(shopify_customer_id))]}},
                "startsAt": datetime.now(timezone.utc).isoformat(),
                "appliesOncePerCustomer": True,
                "combinesWith": {"orderDiscounts": True, "productDiscounts": True},
                "customerGets": {},
            }
        }

        if discount_type == DiscountAmountType.FIXED_AMOUNT:
            variables["basicCodeDiscount"]["customerGets"]["value"] = {
                "discountAmount": {"amount": amount, "appliesOnEachItem": False}
            }
        elif discount_type == DiscountAmountType.PERCENTAGE:
            variables["basicCodeDiscount"]["customerGets"]["value"] = {"percentage": amount}

        if minimum_order_amount and minimum_order_amount > 0:
            variables["basicCodeDiscount"]["minimumRequirement"] = {
                "subtotal": {"greaterThanOrEqualToSubtotal": minimum_order_amount}
            }

        if variant_ids:
            variables["basicCodeDiscount"]["customerGets"]["items"] = {
                "products": {
                    "productVariantsToAdd": [
                        ShopifyService.product_variant_gid(int(variant_id)) for variant_id in variant_ids
                    ]
                }
            }
        else:
            variables["basicCodeDiscount"]["customerGets"]["items"] = {"all": True}

        try:
            body = self.__admin_api_graphql_request(mutation, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to create discount code in shopify store.")

        logger.info(f"Discount code created: {body}")

        shopify_discount = body["data"]["discountCodeBasicCreate"]["codeDiscountNode"]
        shopify_discount_id = shopify_discount["id"].split("/")[-1]
        shopify_discount_code = shopify_discount["codeDiscount"]["codes"]["nodes"][0]["code"]

        return {
            "shopify_discount_id": shopify_discount_id,
            "shopify_discount_code": shopify_discount_code,
        }

    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        status, body = self.__storefront_api_request(
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

    def delete_discount(self, discount_code_gid: str) -> None:
        query = """
        mutation discountCodeDelete($id: ID!) {
          discountCodeDelete(id: $id) {
            deletedCodeDiscountId
            userErrors {
              field
              code
              message
            }
          }
        }
        """
        variables = {"id": discount_code_gid}

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to delete discount code in shopify store.")

    def create_product(
        self, title: str, body_html: str, price: float, sku: str, tags: list[str], requires_shipping: bool = True
    ) -> ShopifyProduct:
        created_product: ShopifyProduct = self.__create_product_with_variant(title, body_html, tags)
        return self.__update_product_variant(created_product.variants[0].gid, price, sku, requires_shipping)

    def create_attendee_discount_product(
        self, title: str, body_html: str, amount: float, sku: str, tags: list[str]
    ) -> ShopifyProduct:
        attendee_discount_product: ShopifyProduct = self.create_product(
            title=title,
            body_html=body_html,
            price=amount,
            sku=sku,
            tags=tags,
            requires_shipping=False,
        )

        self.__publish_and_add_to_online_sales_channel(attendee_discount_product.gid)

        self.__add_image_to_product(attendee_discount_product.gid, self.__gift_image_path)

        return attendee_discount_product

    def create_bundle_identifier_product(self, bundle_id: str) -> ShopifyProduct:
        created_product = self.create_product(f"Bundle #{bundle_id}", "", 0, f"bundle-{bundle_id}", ["hidden"])

        self.__add_image_to_product(created_product.gid, self.__bundle_image_path)
        self.__publish_and_add_to_online_sales_channel(created_product.gid)

        return created_product

    def create_bundle(
        self,
        bundle_name: str,
        bundle_id: str,
        variant_ids: list[str],
        image_src: str = None,
        tags: list[str] = None,
    ) -> str:
        bundle_sku = f"suit-bundle-{bundle_id}"

        bundle_parent_product: ShopifyProduct = self.create_product(
            bundle_name, "", 0.0, bundle_sku, (tags or []) + ["hidden"]
        )

        shopify_variant_gids = [
            ShopifyService.product_variant_gid(int(variant_id)) for variant_id in variant_ids if variant_id
        ]

        self.__add_variants_to_product_bundle(bundle_parent_product.variants[0].gid, shopify_variant_gids)
        self.__publish_and_add_to_online_sales_channel(bundle_parent_product.gid)

        if image_src:
            self.__add_image_to_product(bundle_parent_product.gid, image_src)

        return str(bundle_parent_product.variants[0].get_id())

    def create_bundle2(
        self,
        bundle_name: str,
        bundle_id: str,
        variant_ids: list[str],
        image_src: str = None,
        tags: list[str] = None,
    ) -> ShopifyVariantModel:
        bundle_sku = f"suit-bundle-{bundle_id}"

        bundle_parent_product: ShopifyProduct = self.create_product(
            bundle_name, "", 0.0, bundle_sku, (tags or []) + ["hidden"]
        )

        shopify_variant_gids = [
            ShopifyService.product_variant_gid(int(variant_id)) for variant_id in variant_ids if variant_id
        ]

        self.__add_variants_to_product_bundle(bundle_parent_product.variants[0].gid, shopify_variant_gids)
        self.__publish_and_add_to_online_sales_channel(bundle_parent_product.gid)

        if image_src:
            self.__add_image_to_product(bundle_parent_product.gid, image_src)

        return self.get_variant_by_sku(bundle_sku)

    def deactivate_discount(self, discount_gid: str) -> None:
        query = """
        mutation discountCodeDeactivate($id: ID!) {
          discountCodeDeactivate(id: $id) {
            codeDiscountNode {
              codeDiscount {
                ... on DiscountCodeBasic {
                  title
                  status
                  startsAt
                  endsAt
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

        variables = {"id": discount_gid}

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to deactivate discount code in shopify store.")

    def add_products_to_collection(self, collection_id: int, product_ids: list[int]) -> None:
        query = """
        mutation collectionAddProducts($id: ID!, $productIds: [ID!]!) {
          collectionAddProducts(id: $id, productIds: $productIds) {
            collection {
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
            "id": ShopifyService.collection_gid(collection_id),
            "productIds": [ShopifyService.product_gid(product_id) for product_id in product_ids],
        }

        try:
            self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to add products to collection in shopify store.")

    def __admin_api_graphql_request(self, query: str, variables: dict = None) -> dict:
        response = http(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.__admin_api_access_token,
            },
        )

        response_data = response.data.decode("utf-8")

        if response.status == 429:
            logger.error(f"Shopify API rate limit exceeded. Retry in {response.headers.get('Retry-After')} seconds.")
            raise ShopifyQueryError()
        if response.status >= 400:
            logger.error(f"Shopify API error. Status code: {response.status}, message: {response_data}")
            raise ShopifyQueryError()

        response_body = json.loads(response_data)

        if "errors" in response_body:
            logger.error(f"Shopify API error: {response_data}")
            raise ShopifyQueryError()

        return response_body

    def __storefront_api_request(self, method: str, endpoint: str, body: dict = None):
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

    def __create_product_with_variant(self, title: str, body_html: str, tags: list[str]) -> ShopifyProduct:
        query = """
            mutation productCreate($input: ProductInput!) {
              productCreate(input: $input) {
                product {
                  id
                  title
                  tags
                  variants(first: 1) {
                    edges {
                      node {
                        id
                        title
                        price
                        sku
                      }
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
            "input": {"title": title, "descriptionHtml": body_html, "vendor": "The Modern Groom", "tags": tags}
        }

        try:
            body = self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to create product")

        created_product = body.get("data", {}).get("productCreate", {}).get("product")
        default_variant = created_product.get("variants", {}).get("edges")[0].get("node")

        return ShopifyProduct(
            gid=created_product.get("id"),
            title=created_product.get("title"),
            tags=created_product.get("tags"),
            variants=[
                ShopifyVariant(
                    gid=default_variant.get("id"),
                    title=default_variant.get("title"),
                    price=default_variant.get("price"),
                    sku=default_variant.get("sku"),
                )
            ],
        )

    def __update_product_variant(
        self,
        variant_gid: str,
        price: float,
        sku: str,
        requires_shipping: bool = True,
    ) -> ShopifyProduct:
        query = """
        mutation productVariantUpdate($input: ProductVariantInput!) {
          productVariantUpdate(input: $input) {
            product {
              id
              title
              tags
              variants(first: 1) {
                edges {
                  node {
                    id
                    title
                    price
                    sku
                  }
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
            "input": {
                "id": variant_gid,
                "price": price,
                "sku": sku,
                "requiresShipping": requires_shipping,
            }
        }

        try:
            body = self.__admin_api_graphql_request(query, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to update variant")

        created_product = body.get("data", {}).get("productVariantUpdate", {}).get("product")
        default_variant = created_product.get("variants", {}).get("edges")[0].get("node")

        return ShopifyProduct(
            gid=created_product.get("id"),
            title=created_product.get("title"),
            tags=created_product.get("tags"),
            variants=[
                ShopifyVariant(
                    gid=default_variant.get("id"),
                    title=default_variant.get("title"),
                    price=default_variant.get("price"),
                    sku=default_variant.get("sku"),
                )
            ],
        )

    def __add_variants_to_product_bundle(self, parent_product_shopify_variant_gid: str, variants: list[str]) -> None:
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
                    "parentProductVariantId": parent_product_shopify_variant_gid,
                    "productVariantRelationshipsToCreate": bundle_variants,
                }
            ]
        }

        try:
            self.__admin_api_graphql_request(mutation, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to create product bundle in shopify store.")

    def __publish_and_add_to_online_sales_channel(self, product_gid: str) -> None:
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
                "id": product_gid,
                "publishedAt": datetime.now(timezone.utc).isoformat(),
                "productPublications": {
                    "publicationId": self.__online_store_sales_channel_id,
                    "publishDate": datetime.now(timezone.utc).isoformat(),
                },
            },
        }

        try:
            self.__admin_api_graphql_request(mutation, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to publish product in shopify store.")

    def __add_image_to_product(self, product_gid: str, image_url: str) -> None:
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
            "productId": product_gid,
        }

        try:
            self.__admin_api_graphql_request(mutation, variables)
        except ShopifyQueryError:
            raise ServiceError(f"Failed to add image to product in shopify store.")
