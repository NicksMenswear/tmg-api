import requests
import os
from werkzeug.exceptions import HTTPException
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.realpath(__file__))

env_file_path = os.path.join(current_dir, '../../.env')

load_dotenv(dotenv_path=env_file_path)
shopify_store = os.getenv('shopify_store')
client_id = os.getenv('client_id')
admin_api_access_token = os.getenv('admin_api_access_token')
client_secret = os.getenv('client_secret')
api_version = os.getenv('api_version')


def search_customer_by_email(email,access_token):
    try:
        response = requests.get(
            f'https://{shopify_store}.myshopify.com/admin/api/2024-01/customers/search.json',
            params={'query': f'email:{email}'},
            headers={
                'Content-Type': 'application/json',
                'X-Shopify-Access-Token': access_token,
            }
        )
        customers = response.json().get('customers',[])
        return customers
    except requests.exceptions.RequestException as error:
        print('Error searching for customer by email:', error)
        raise

def create_shopify_customer(customer_data):
    try:
        response = requests.post(
            f'https://{shopify_store}.myshopify.com/admin/api/2024-01/customers.json',
            json={
                'customer': customer_data
            },
            headers={
                'Content-Type': 'application/json',
                'X-Shopify-Access-Token': admin_api_access_token,
            }
        )
        created_customer = response.json().get('customer', {})
        return created_customer
    except requests.exceptions.RequestException as error:
        print('Error creating customer:', error)
        raise

def get_access_token():
    try:
        response = requests.post(
            f'https://{shopify_store}.myshopify.com/admin/oauth/access_token',
            json={
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'client_credentials',
            }
        )

        access_token = response.json().get('access_token')
        return access_token
    except requests.exceptions.RequestException as error:
        print('Error getting access token:', error)
        raise

def get_customer(email):

    try:
        access_token = get_access_token()
        customers = search_customer_by_email(email,access_token)
        return customers
    except Exception as error:
        print(error)

def list_customer():

    customer_email = 'syed@nicksmenswear.com'

    try:
        access_token = get_access_token()
        customers = search_customer_by_email(customer_email,access_token)
        print('Found customers: ', customers)
    except Exception as error:
        print(error)

def get_activation_url(customer_id):
    try:
        access_token = get_access_token()
        url = f'https://{shopify_store}.myshopify.com/admin/api/{api_version}/customers/{customer_id}/account_activation_url.json'
        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': admin_api_access_token,
        }

        response = requests.post(url, headers=headers)
        print(response)
        if response.status_code == 200:
            activation_url = response.json().get('account_activation_url')
            print(f'Activation URL: {activation_url}')
            return activation_url
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

def create_customer(customer_data):
    try:
        created_customer = create_shopify_customer(customer_data)
        if created_customer:
            print('Created customer:', created_customer['id'])
            return created_customer['id']
    except Exception as error:
        print(error)
