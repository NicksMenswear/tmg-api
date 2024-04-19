import urllib3
import json
import os

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
    response = urllib3.request("POST", URL, headers=headers, body=data)
    if response.status == 422:
        return "Already exist", 422

    response_data = json.loads(response.data.decode("utf-8"))
    contact_value = response_data.get("contact", {}).get("id")

    print("Contact Value:", contact_value)

    if contact_value:
        url = "https://themoderngroom.api-us1.com/api/3/contactAutomations"
        body_data = {"contactAutomation": {"contact": str(contact_value), "automation": "189"}}
        data = json.dumps(body_data)
        response = urllib3.request("POST", url, headers=headers, data=data)
        if response.status == 422:
            return "Already exist", 422
        elif response.status == 200 or response.status == 201:
            return "created contact in automation successfully", 201
    else:
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

    print(" ======================== Contact details: ", contact_details)
    data = json.dumps(contact_details)
    response = urllib3.request("POST", URL, headers=headers, data=data)
    if response.status == 422:
        return "Already exist", 422

    response_data = json.loads(response.data.decode("utf-8"))
    contact_value = response_data.get("contact", {}).get("id")

    print("Contact Value:", contact_value)

    if contact_value:
        url = "https://themoderngroom.api-us1.com/api/3/contactAutomations"
        body_data = {"contactAutomation": {"contact": str(contact_value), "automation": "189"}}
        data = json.dumps(body_data)
        response = urllib3.request("POST", url, headers=headers, data=data)
        if response.status == 422:
            return "Already exist", 422
        elif response.status == 200 or response.status == 201:
            return "created contact in automation successfully", 201
    else:
        return "Internal Server Error", 500
