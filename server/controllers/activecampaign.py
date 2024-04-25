import json
import logging
import os

from server.controllers.util import http

logger = logging.getLogger(__name__)


URL = "https://themoderngroom.api-us1.com/api/3/contacts"
API_KEY = os.getenv("API_KEY")


def create_contact(data):
    headers = {"accept": "*/*", "content-type": "application/json", "Api-Token": API_KEY}

    contact_details = {
        "contact": {
            "email": data["email"],
            # "first_name": data['first_name'],
            # "last_name": data['last_name'],
            "fieldValues": [
                {
                    "event_name": data["event_name"],
                    "event_id": data["event_id"],
                    "activation-url": data["activation_url"],
                }
            ],
        }
    }

    data = json.dumps(contact_details)
    response = http("POST", URL, headers=headers, body=data)
    if response.status == 422:
        return "Already exist", 422

    response_data = json.loads(response.data.decode("utf-8"))
    contact_value = response_data.get("contact", {}).get("id")

    logger.info(f"Contact Value: {contact_value}")

    if contact_value:
        url = "https://themoderngroom.api-us1.com/api/3/contactAutomations"
        body_data = {"contactAutomation": {"contact": str(contact_value), "automation": "189"}}
        data = json.dumps(body_data)
        response = http("POST", url, headers=headers, data=data)
        if response.status == 422:
            return "Already exist", 422
        elif response.status == 200 or response.status == 201:
            return "created contact in automation successfully", 201
    else:
        logger.error("No contact_value found.")
        return "Internal Server Error", 500


def create_contact_user(data):
    headers = {"accept": "*/*", "content-type": "application/json", "Api-Token": API_KEY}

    contact_details = {
        "contact": {
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "fieldValues": [
                {
                    # "event_name": data['event_name'],
                    # "event_id": data['event_id'],
                    "activation-url": data["activation_url"]
                }
            ],
        }
    }

    logger.info(f"Contact details: {contact_details}")
    data = json.dumps(contact_details)
    response = http("POST", URL, headers=headers, data=data)
    if response.status == 422:
        return "Already exist", 422

    response_data = json.loads(response.data.decode("utf-8"))
    contact_value = response_data.get("contact", {}).get("id")

    logger.info(f"Contact Value: {contact_value}")

    if contact_value:
        url = "https://themoderngroom.api-us1.com/api/3/contactAutomations"
        body_data = {"contactAutomation": {"contact": str(contact_value), "automation": "189"}}
        data = json.dumps(body_data)
        response = http("POST", url, headers=headers, data=data)
        if response.status == 422:
            return "Already exist", 422
        elif response.status == 200 or response.status == 201:
            return "created contact in automation successfully", 201
    else:
        return "Internal Server Error", 500
