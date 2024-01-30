import requests
import base64

shopify_store = "quickstart-a91e1214"
client_id = "2c9f6cdd262407fd70b99dc1c514b0ea"
client_secret = "60d3cef8fd04190f9d5f4ec3a00d323a"
api_version = "2024-01"


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

def create_shopify_customer(customer_data, access_token):
    try:
        response = requests.post(
            f'https://{shopify_store}.myshopify.com/admin/api/2024-01/customers.json',
            json=customer_data,
            headers={
                'Content-Type': 'application/json',
                'X-Shopify-Access-Token': access_token,
            }
        )
        print('------------------- Response: ',response)
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

def list_customer():
    
    customer_email = 'syed@nicksmenswear.com'
    try:
        access_token = get_access_token()
        customers = search_customer_by_email(customer_email,access_token)
        print('Found customers: ', customers)
    except Exception as error:
        print(error)

def create_customer(customer_data):
    try:
        print('In create customer-----------------------------')
        access_token = get_access_token()
        print("------------------------   access token: ", access_token)
        created_customer = create_shopify_customer(customer_data, access_token)
        print("-------------------------- Creat Response: ",created_customer)
        if created_customer:
            print('Created customer:', created_customer)
    except Exception as error:
        print(error)
