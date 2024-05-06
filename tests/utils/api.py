import json

import requests

from . import API_PARAMS, ACTIVE_ENV, API_HEADERS

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


def get_all_events_by_email(email):
    response = requests.get(f"{BASE_API_URL}/users/{email}", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)
    user_id = response.json().get("id")

    response = requests.get(f"{BASE_API_URL}/users/{user_id}/events", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 200:
        return response.json()

    raise Exception(f"Failed to get events by email: {email}")


def delete_event(event_id):
    response = requests.delete(f"{BASE_API_URL}/events/{event_id}", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 204:
        return

    raise Exception(f"Failed to delete event by event_id: {event_id}")


def delete_all_events(email):
    events = get_all_events_by_email(email)

    for event in events:
        delete_event(event["id"])
