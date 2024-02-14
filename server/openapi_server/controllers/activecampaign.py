from activecampaign.client import Client
import requests
import json
from dotenv import load_dotenv
import os


load_dotenv()


URL = "https://themoderngroom.api-us1.com/api/3/contacts"
API_KEY = os.getenv('API_KEY')

client = Client(URL,API_KEY)

def create_contact(data):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Api-Token":  API_KEY
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

    print('----------------------- Contact  Rresponse: ',response.text)
