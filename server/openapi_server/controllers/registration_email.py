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
# import smtplib
# from email.mime.text import MIMEText

# def send_email(subject ,body, sender_email ,receiver_email, password):
#     try:
#         # Construct the email message
#         msg = MIMEText(body)
#         msg['From'] = sender_email
#         msg['To'] = receiver_email
#         msg['Subject'] = subject
#         with smtplib.SMTP_SSL('smtp.gmail.com' , 465) as smtp_server:
#             smtp_server.login(sender_email , password)
#             smtp_server.sendmail(sender_email,receiver_email ,msg.as_string())
#             print('message sent')


#     except Exception as e:
#         print(f"Failed to send email. Error: {str(e)}")



def send_email(customer_id, activation_url, receiver_email):
    try:
        url = f'https://{shopify_store}.myshopify.com/admin/api/{api_version}/customers/{customer_id}/send_invite.json'
        headers = {
            'Content-Type': 'application/json',
            'X-Shopify-Access-Token': admin_api_access_token,
        }
        body = {
            "customer_invite": {
                "to": receiver_email,
                "from": "eng@themoderngroom.com",
                "subject": "Welcome to my new shop",
                "custom_message": f'welcome to My awesome new store '
            }
        }

        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            activation_url = response.json().get('account_activation_url')
            print(f'Activation URL: {activation_url}')
            return activation_url
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

