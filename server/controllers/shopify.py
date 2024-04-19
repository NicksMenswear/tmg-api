import urllib3
import json
import os

from server.database.models import User
from server.database.database_manager import get_database_session


shopify_store = os.getenv("shopify_store")
client_id = os.getenv("client_id")
admin_api_access_token = os.getenv("admin_api_access_token")
client_secret = os.getenv("client_secret")
api_version = os.getenv("api_version")

db = get_database_session()


def search_customer_by_email(email):
    try:
        user = db.query(User).filter(User.email == email).first()
        response = urllib3.request(
            "GET",
            f"https://{shopify_store}.myshopify.com/admin/api/2024-01/customers/{user.shopify_id}.json",
            headers={
                "X-Shopify-Access-Token": admin_api_access_token,
            },
        )
        response.raise_for_status()
        customers = json.loads(response.data.decode("utf-8")).get("customers", [])
        return customers
    except urllib3.exceptions.RequestError as error:
        print("Error searching for customer by email:", error)
        raise


def create_shopify_customer(customer_data):
    response = urllib3.request(
        "POST",
        f"https://{shopify_store}.myshopify.com/admin/api/2024-01/customers.json",
        json={"customer": customer_data},
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": admin_api_access_token,
        },
    )
    created_customer = json.loads(response.data.decode("utf-8")).get("customer", {})
    return created_customer


def get_access_token():
    try:
        response = urllib3.request(
            "POST",
            f"https://{shopify_store}.myshopify.com/admin/oauth/access_token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        access_token = response.json().get("access_token")
        return access_token
    except urllib3.exceptions.RequestError as error:
        print("Error searching for customer by email:", error)
        raise


def get_customer(email):
    try:
        customers = search_customer_by_email(email)
        return customers
    except Exception as e:
        print(f"An error occurred: {e}")


# TODO delete this function
def list_customer():
    customer_email = "syed@nicksmenswear.com"
    try:
        customers = search_customer_by_email(customer_email)
        print("Found customers: ", customers)
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


def get_activation_url(customer_id):
    try:
        url = f"https://{shopify_store}.myshopify.com/admin/api/{api_version}/customers/{customer_id}/account_activation_url.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": admin_api_access_token,
        }
        response = urllib3.request("POST", url, headers=headers)
        if response.status == 200:
            activation_url = json.loads(response.data.decode("utf-8")).get("account_activation_url")
            print(f"Activation URL: {activation_url}")
            return activation_url
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


def create_customer(customer_data):
    created_customer = create_shopify_customer(customer_data)
    if created_customer:
        print("Created customer:", created_customer["id"])
        return created_customer["id"]
