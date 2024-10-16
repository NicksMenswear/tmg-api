import enum
import fnmatch
import json
import logging
import os
import random
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Set, Dict

from server.controllers.util import http
from server.flask_app import FlaskApp
from server.models.shopify_model import ShopifyCustomer, ShopifyVariantModel, ShopifyProduct, ShopifyVariant
from server.services import ServiceError, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)


class DiscountAmountType(enum.Enum):
    FIXED_AMOUNT = "fixed_amount"
    PERCENTAGE = "percentage"


class AbstractShopifyService(ABC):
    @abstractmethod
    def get_account_login_url(self) -> str:
        pass

    @abstractmethod
    def get_account_activation_url(self, customer_id: int) -> str:
        pass

    @abstractmethod
    def get_customer_by_email(self, email: str) -> Optional[ShopifyCustomer]:
        pass

    @abstractmethod
    def get_customers_by_email_pattern(self, email_pattern: str, num_customers_to_fetch=100) -> List[ShopifyCustomer]:
        pass

    @abstractmethod
    def create_customer(self, first_name: str, last_name: str, email: str) -> ShopifyCustomer:
        pass

    @abstractmethod
    def update_customer(
        self, customer_gid: str, first_name: str, last_name: str, email: str, phone_number: str = None
    ) -> ShopifyCustomer:
        pass

    @abstractmethod
    def delete_customer(self, customer_gid: str) -> None:
        pass

    @abstractmethod
    def add_tags(self, shopify_gid: str, tags: Set[str]) -> None:
        pass

    @abstractmethod
    def remove_tags(self, shopify_gid: str, tags: Set[str]) -> None:
        pass

    @abstractmethod
    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        pass

    @abstractmethod
    def archive_product(self, product_gid: str) -> None:
        pass

    @abstractmethod
    def delete_product(self, product_gid: str) -> None:
        pass

    @abstractmethod
    def get_variants_by_id(self, variant_ids: List[str]) -> List[ShopifyVariantModel]:
        pass

    @abstractmethod
    def create_discount_code(
        self,
        title: str,
        code: str,
        shopify_customer_id: str,
        discount_type: DiscountAmountType,
        amount: float,
        minimum_order_amount: Optional[int] = None,
        variant_ids: Optional[List[str]] = None,
    ):
        pass

    @abstractmethod
    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        pass

    @abstractmethod
    def delete_discount(self, discount_code_id: int) -> None:
        pass

    @abstractmethod
    def create_product(
        self, title: str, body_html: str, price: float, sku: str, tags: List[str], requires_shipping: bool = True
    ) -> ShopifyProduct:
        pass

    @abstractmethod
    def create_attendee_discount_product(
        self, title: str, body_html: str, amount: float, sku: str, tags: List[str]
    ) -> ShopifyProduct:
        pass

    @abstractmethod
    def create_bundle(
        self, bundle_name: str, bundle_id: str, variant_ids: List[str], image_src: str = None, tags: List[str] = None
    ) -> str:
        pass

    @abstractmethod
    def create_bundle_identifier_product(self, bundle_id: str) -> ShopifyProduct:
        pass


class FakeShopifyService(AbstractShopifyService):
    def __init__(self, shopify_virtual_products=None, shopify_virtual_product_variants=None, shopify_variants=None):
        self.shopify_variants = shopify_variants if shopify_variants else {}
        self.shopify_virtual_products = shopify_virtual_products if shopify_virtual_products else {}
        self.shopify_virtual_product_variants = (
            shopify_virtual_product_variants if shopify_virtual_product_variants else {}
        )
        self.customers: Dict[str, ShopifyCustomer] = {}

    def get_account_login_url(self) -> str:
        pass

    def get_account_activation_url(self, customer_id: int) -> str:
        pass

    def get_customer_by_email(self, email: str) -> Optional[ShopifyCustomer]:
        if email.endswith("@shopify-user-does-not-exists.com"):
            return None

        for customer in self.customers.values():
            if customer.email == email:
                return customer

        return None

    def get_customers_by_email_pattern(self, email_pattern: str, num_customers_to_fetch=100) -> List[ShopifyCustomer]:
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
        self, customer_gid: str, first_name: str, last_name: str, email: str, phone_number: str = None
    ) -> ShopifyCustomer:
        pass

    def delete_customer(self, customer_gid: str) -> None:
        for email, customer in self.customers.items():
            if customer.gid == customer_gid:
                del self.customers[customer.gid]
                break

    def add_tags(self, shopify_gid: str, tags: Set[str]) -> None:
        customer = self.customers.get(shopify_gid)

        if not customer:
            raise NotFoundError(f"Customer with id {shopify_gid} not found.")

        customer.tags = list(set(customer.tags) | tags)

    def remove_tags(self, shopify_gid: str, tags: Set[str]) -> None:
        customer = self.customers.get(shopify_gid)

        if not customer:
            raise NotFoundError(f"Customer with id {shopify_gid} not found.")

        customer.tags = list(set(customer.tags) - set(tags))

    def get_variant_by_sku(self, sku: str) -> ShopifyVariantModel:
        return self.shopify_variants[random.choice(list(self.shopify_variants.keys()))]

    def get_variants_by_id(self, variant_ids: List[str]) -> List[ShopifyVariantModel]:
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
        minimum_order_amount: Optional[int] = None,
        variant_ids: Optional[List[str]] = None,
    ):
        return {
            "shopify_discount_code": code,
            "shopify_discount_id": random.randint(1000, 100000),
        }

    def apply_discount_codes_to_cart(self, cart_id, discount_codes):
        pass

    def delete_discount(self, discount_code_id: int) -> None:
        pass

    def create_product(
        self, title: str, body_html: str, price: float, sku: str, tags: List[str], requires_shipping: bool = True
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
        self, title: str, body_html: str, amount: float, sku: str, tags: List[str]
    ) -> ShopifyProduct:
        return self.create_product(title, body_html, amount, sku, tags, False)

    def create_bundle(
        self, bundle_name: str, bundle_id: str, variant_ids: List[str], image_src: str = None, tags: List[str] = None
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
            }
        )

        self.shopify_variants[bundle_variant_id] = bundle_model

        return bundle_model.variant_id

    def create_bundle_identifier_product(self, bundle_id: str) -> ShopifyProduct:
        return self.create_product(
            title=f"Bundle #{bundle_id}",
            body_html="",
            price=0.0,
            sku=f"bundle-{bundle_id}",
            tags=[],
        )


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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            body={"query": query, "variables": variables},
        )

        if status >= 400 or "errors" in body:
            raise ServiceError(f"Failed to create activation url")

        return body.get("data", {}).get("customerGenerateAccountActivationUrl", {}).get("accountActivationUrl")

    def get_customer_by_email(self, email: str) -> Optional[ShopifyCustomer]:
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            body={"query": query, "variables": variables},
        )

        if status >= 400 or "errors" in body:
            raise ServiceError("Failed to get customer")

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

    def get_customers_by_email_pattern(self, email_pattern: str, num_customers_to_fetch=100) -> List[ShopifyCustomer]:
        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {
                "query": f'{{ customers(first: {num_customers_to_fetch}, query: "email:{email_pattern}") {{ edges {{ node {{ id email firstName lastName state tags }} }} }} }}'
            },
        )

        if status >= 400:
            raise ServiceError(f"Failed to get customers by email suffix in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to get customers by email suffix in shopify store. {body['errors']}")

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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query, "variables": variables},
        )

        user_errors = body.get("data", {}).get("customerCreate", {}).get("userErrors", [])

        if status >= 400:
            raise ServiceError(f"Failed to create customer")

        if user_errors:
            for error in user_errors:
                if "email has already been taken" in error.get("message", "").lower():
                    raise DuplicateError("Shopify customer with this email address already exists.")

            raise ServiceError("Failed to create shopify customer.")

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
        self, customer_gid: str, first_name: str, last_name: str, email: str, phone_number: str = None
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

        variables = {"input": customer_input}

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            body={"query": query, "variables": variables},
        )

        if status >= 400:
            raise ServiceError("Failed to update shopify customer.")

        user_errors = body.get("data", {}).get("customerUpdate", {}).get("userErrors", [])

        if user_errors:
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
        mutation = """
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to delete customer in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to delete customer in shopify store. {body['errors']}")

    def add_tags(self, shopify_gid: str, tags: Set[str]) -> None:
        mutation = """
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to add tags in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to add tags in shopify store. {body['errors']}")

    def remove_tags(self, shopify_gid: str, tags: Set[str]) -> None:
        mutation = """
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to remove tags in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to remove tags in shopify store. {body['errors']}")

    def get_variant_by_sku(self, sku: str) -> Optional[ShopifyVariantModel]:
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

        status, body = self.__admin_api_request(
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

        status, body = self.__admin_api_request(
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to archive product by id '{product_gid}'. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to archive product by id '{product_gid}': {body['errors']}")

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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to delete product by id '{product_gid}'. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to delete product by id '{product_gid}': {body['errors']}")

    def create_discount_code(
        self,
        title: str,
        code: str,
        shopify_customer_id: str,
        discount_type: DiscountAmountType,
        amount: float,
        minimum_order_amount: Optional[int] = None,
        variant_ids: Optional[List[str]] = None,
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

        status, body = self.__admin_api_request(
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

    def delete_discount(self, discount_code_id: int) -> None:
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
        variables = {"id": f"gid://shopify/DiscountCodeNode/{discount_code_id}"}

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to delete discount code in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to delete discount code in shopify store: {body['errors']}")

        return body

    def create_product(
        self, title: str, body_html: str, price: float, sku: str, tags: List[str], requires_shipping: bool = True
    ) -> ShopifyProduct:
        created_product: ShopifyProduct = self.__create_product_with_variant(title, body_html, tags)
        return self.__update_product_variant(created_product.variants[0].gid, price, sku, requires_shipping)

    def create_attendee_discount_product(
        self, title: str, body_html: str, amount: float, sku: str, tags: List[str]
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
        created_product = self.create_product(f"Bundle #{bundle_id}", "", 0, f"bundle-{bundle_id}", ["hidden"], True)

        self.__add_image_to_product(created_product.gid, self.__bundle_image_path)
        self.__publish_and_add_to_online_sales_channel(created_product.gid)

        return created_product

    def create_bundle(
        self, bundle_name: str, bundle_id: str, variant_ids: List[str], image_src: str = None, tags: List[str] = None
    ) -> str:
        bundle_parent_product: ShopifyProduct = self.__create_bundle_product(
            bundle_name, f"suit-bundle-{bundle_id}", tags or []
        )

        shopify_variant_gids = [
            ShopifyService.product_variant_gid(int(variant_id)) for variant_id in variant_ids if variant_id
        ]

        self.__add_variants_to_product_bundle(bundle_parent_product.variants[0].gid, shopify_variant_gids)
        self.__publish_and_add_to_online_sales_channel(bundle_parent_product.gid)

        if image_src:
            self.__add_image_to_product(bundle_parent_product.gid, image_src)

        return str(bundle_parent_product.variants[0].get_id())

    def __admin_api_request(self, method: str, endpoint: str, body: dict = None):
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

    def __create_product_with_variant(self, title: str, body_html: str, tags: List[str]) -> ShopifyProduct:
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product: {body['errors']}")

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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": query, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to update variant price. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to update variant price: {body['errors']}")

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

    def __create_bundle_product(self, product_name: str, handle: str, tags: List[str]) -> ShopifyProduct:
        mutation = """
        mutation CreateProductBundle($input: ProductInput!) {
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
            userErrors{
              field
              message
            }
          }
        }
        """
        variables = {"input": {"title": product_name, "handle": handle, "variants": [], "tags": ["hidden"] + tags}}

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product bundle in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product bundle in shopify store. {body['errors']}")

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

    def __add_variants_to_product_bundle(self, parent_product_shopify_variant_gid: str, variants: List[str]):
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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product bundle in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product bundle in shopify store. {body['errors']}")

        return body

    def __publish_and_add_to_online_sales_channel(self, parent_product_gid: str):
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
                "id": parent_product_gid,
                "publishedAt": datetime.now(timezone.utc).isoformat(),
                "productPublications": {
                    "publicationId": self.__online_store_sales_channel_id,
                    "publishDate": datetime.now(timezone.utc).isoformat(),
                },
            },
        }

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to create product bundle in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to create product bundle in shopify store. {body['errors']}")

        return body

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

        status, body = self.__admin_api_request(
            "POST",
            f"{self.__shopify_graphql_admin_api_endpoint}/graphql.json",
            {"query": mutation, "variables": variables},
        )

        if status >= 400:
            raise ServiceError(f"Failed to add image to product in shopify store. Status code: {status}")

        if "errors" in body:
            raise ServiceError(f"Failed to add image to product in shopify store. {body['errors']}")
