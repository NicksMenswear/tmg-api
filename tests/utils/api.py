import json

import requests

ACTIVE_ENV = "stg"

API_PARAMS = {
    "dev": {
        "url": "https://api.dev.tmgcorp.net",
        "hmac": {
            "logged_in_customer_id": "7061007532163",
            "path_prefix": "/apps/dev",
            "shop": "quickstart-a91e1214.myshopify.com",
            "signature": "9e655406dc5d9cedb399ecae73c642a5cc7410a5a083fc4fb8d250ec56922476",
            "timestamp": "1713866190",
        },
    },
    "stg": {
        "url": "https://api.stg.tmgcorp.net",
        "hmac": {
            "logged_in_customer_id": "6519862853674",
            "path_prefix": "/apps/prod",
            "shop": "themodern-groom.myshopify.com",
            "signature": "945b5cc30592e6d967717cee1a66da445d2ac6222971cfe645d72268ca66b8d3",
            "timestamp": "1713351981",
        },
    },
}

API_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

BASE_API_URL = API_PARAMS[ACTIVE_ENV]["url"]
API_HMAC_QUERY_PARAMS = API_PARAMS[ACTIVE_ENV]["hmac"]


def get_all_events_by_email(email):
    response = requests.get(f"{BASE_API_URL}/events/{email}", params=API_HMAC_QUERY_PARAMS, headers=API_HEADERS)

    if response.status_code == 200:
        return response.json()

    raise Exception(f"Failed to get events by email: {email}")


def delete_event(event_id, user_id):
    response = requests.put(
        f"{BASE_API_URL}/delete_events",
        params=API_HMAC_QUERY_PARAMS,
        headers=API_HEADERS,
        data=json.dumps({"event_id": event_id, "user_id": user_id, "is_active": False}),
    )

    if response.status_code == 204:
        return

    raise Exception(f"Failed to delete event by event_id/user_id: {event_id}/{user_id}")


def delete_all_events(email):
    events = get_all_events_by_email(email)

    for event in events:
        delete_event(event["id"], event["user_id"])
