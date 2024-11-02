import os
from typing import Any

import requests

SHOPIFY_STORE_HOST = os.getenv("SHOPIFY_STORE_HOST", "quickstart-a91e1214.myshopify.com")
SHOPIFY_GRAPHQL_API_ENDPOINT = f"https://{SHOPIFY_STORE_HOST}/admin/api/2024-07/graphql.json"
SHOPIFY_ADMIN_API_ACCESS_TOKEN = os.getenv("SHOPIFY_ADMIN_API_ACCESS_TOKEN")


def _admin_api_graphql_request(query: str, variables: dict[str, Any] = None) -> dict[str, Any]:
    response = requests.post(
        SHOPIFY_GRAPHQL_API_ENDPOINT,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": SHOPIFY_ADMIN_API_ACCESS_TOKEN},
    )

    if response.status_code != 200:
        raise Exception(f"Shopify API error: {response.status_code}, {response.text}")

    response_data = response.json()

    if "errors" in response_data:
        raise Exception(f"Shopify API error: {response.status_code}, {str(response.text)}")

    return response_data


def get_variant_by_id(variant_gid: str) -> dict[str, Any]:
    query = """
        query getProductVariantAndProduct($variantId: ID!) {
            node(id: $variantId) {
                ... on ProductVariant {
                    id
                    title
                    sku
                    price
                    product {
                        id
                        title
                        tags
                    }
                }
            }
        }
    """

    variables = {"variantId": variant_gid}

    body = _admin_api_graphql_request(query, variables)

    return body.get("data", {}).get("node", {})


def get_customer_by_id(customer_gid: str) -> dict[str, Any]:
    query = """
        query getCustomer($customerId: ID!) {
            node(id: $customerId) {
                ... on Customer {
                    id
                    email
                    firstName
                    lastName
                    tags
                }
            }
        }
    """

    variables = {"customerId": customer_gid}

    body = _admin_api_graphql_request(query, variables)

    return body.get("data", {}).get("node", {})
