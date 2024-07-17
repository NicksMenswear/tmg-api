import json

import requests

from server.controllers.events import EVENT_FORCE_DELETE_HEADER
from server.models.look_model import ProductSpecType
from server.tests.e2e import API_PARAMS, ACTIVE_ENV, API_HEADERS

BASE_API_URL = API_PARAMS[ACTIVE_ENV]["url"]
API_HMAC_QUERY_PARAMS = API_PARAMS[ACTIVE_ENV]["hmac"]


def create_user(first_name, last_name, email, account_status=True):
    response = requests.post(
        f"{BASE_API_URL}/users",
        params=API_HMAC_QUERY_PARAMS,
        headers=API_HEADERS,
        data=json.dumps(
            {"first_name": first_name, "last_name": last_name, "email": email, "account_status": account_status}
        ),
    )

    if response.status_code == 201:
        return

    raise Exception(f"Failed to create user - {first_name}/{last_name}/{email}")


def get_user_by_email(email):
    # encoded_email = urllib.parse.quote(email)
    response = requests.get(f"{BASE_API_URL}/users/{email}", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 200:
        return response.json()

    raise Exception(f"Failed to get user by email: {email}")


def get_all_events_by_email(email):
    user_id = get_user_by_email(email).get("id")

    response = requests.get(f"{BASE_API_URL}/users/{user_id}/events", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 200:
        return response.json()

    raise Exception(f"Failed to get events by email: {email}")


def delete_event(event_id):
    response = requests.delete(
        f"{BASE_API_URL}/events/{event_id}",
        params=API_HMAC_QUERY_PARAMS,
        headers={**API_HEADERS, EVENT_FORCE_DELETE_HEADER: "true"},
    )

    if response.status_code == 204:
        return

    raise Exception(f"Failed to delete event by event_id: {event_id}")


def delete_all_events(email):
    events = get_all_events_by_email(email)

    for event in events:
        delete_event(event["id"])


def get_all_looks(user_id):
    response = requests.get(f"{BASE_API_URL}/users/{user_id}/looks", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 200:
        return response.json()

    raise Exception(f"Failed to get looks by user_id: {user_id}")


def delete_all_looks(user_id):
    looks = get_all_looks(user_id)

    if not looks:
        return

    for look in looks:
        delete_look(look.get("id"))


def delete_look(look_id):
    response = requests.delete(f"{BASE_API_URL}/looks/{look_id}", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 204:
        return

    raise Exception(f"Failed to delete look by look_id: {look_id}")


def create_look(look_name, user_id, product_specs=None):
    response = requests.post(
        f"{BASE_API_URL}/looks",
        params=API_HMAC_QUERY_PARAMS,
        headers=API_HEADERS,
        data=json.dumps(
            {
                "name": look_name,
                "user_id": user_id,
                "spec_type": ProductSpecType.SKU,
                "product_specs": (
                    product_specs
                    if product_specs
                    else {
                        "suit_variant": "001A2BLK",  # Black Suit
                        "variants": [
                            "001A2BLK",  # Black Suit
                            "403A2WHT",  # White Shirt
                            "603A40NI",  # Apple Red Neck Tie
                            "703A4BLK",  # Black Adjustable Belt
                            "803A4BLK",  # Black Dress Shoes
                            "903A4BLK",  # Solid Black Dress Socks
                        ],
                    }
                ),
            }
        ),
    )

    if response.status_code == 201:
        return response.json()

    raise Exception(f"Failed to create look - {look_name}/{user_id}")


def get_user_activation_url(user_id):
    response = requests.get(
        f"{BASE_API_URL}/users/{user_id}/activation-url", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS
    )

    print("Response: " + str(response.json()))

    if response.status_code == 200:
        return response.json().get("activation_url")

    raise Exception(f"Failed to get user activation url by user_id: {user_id}")
