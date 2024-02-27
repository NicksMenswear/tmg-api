import requests
import json
from dotenv import load_dotenv
import os


load_dotenv()


URL = "https://themoderngroom.api-us1.com/api/3/contacts"
API_KEY = os.getenv('API_KEY')


def create_contact(data):
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "Api-Token": API_KEY
    }

    contact_details = {
        "contact": {
            "email": data['email'],
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "fieldValues": [  
                {
                    "event_name": data['event_name'], 
                    "event_id": data['event_id'],
                    "activation-url": data['activation_url']
                }
            ]
        }
    }

    data = json.dumps(contact_details)
    response = requests.post(URL,headers=headers,data=data)

    response_data = response.json()

    if response.status_code == 422:
        return "Already exist", 422
    contact_value = response_data.get('contact', {}).get('id')

    print("Contact Value:", contact_value) 

    if contact_value:
        url = "https://themoderngroom.api-us1.com/api/3/contactAutomations"
        body_data = {
            "contactAutomation": {
                "contact": str(contact_value),
                "automation": "189"
            }
        }
        data = json.dumps(body_data)
        response = requests.post(url, headers=headers , data=data)
        print('------------------ Automation Response: ', response.status_code
              )
        if response.status_code == 422:
            return "Already exist", 422
        elif response.status_code == 200 or response.status_code == 201:
            return "created contact in automation successfully", 201
    else:
        return "Internal Server Error"

