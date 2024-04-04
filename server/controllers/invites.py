from server.database.database_manager import get_database_session  # noqa: E501
from server.database.models import User
from server.controllers.shopify import get_activation_url, create_customer, get_customer
from server.controllers.registration_email import send_email
from server.controllers.activecampaign import create_contact
from server.controllers.hmac_1 import hmac_verification
import os


sender_email = os.getenv('sender_email')
password = os.getenv('sender_password')
db = get_database_session()

@hmac_verification()
def send_invite(invite_data):  # noqa: E501
    """Send Invite

     # noqa: E501

    Customer-id
    First Name
    Last Name
    Customer email
    Event-id
    Event Name

    :rtype: None
    """
    try:
        if 'data' in invite_data:
            for attendee in invite_data['data']:
                existing_user = db.query(User).filter(User.email == attendee['email']).first()
                if not existing_user.account_status:
                    activation_url = get_activation_url(existing_user.shopify_id)
                    activation_link = f'<a href="{activation_url}">Click Me</a>'
                    body = f"You have been invited to an event. Click the following link to activate your account: {activation_link}"
                    sender_password=password
                    reciever = attendee['email']
                    subject ='Wedding Invite'
                    send_email(subject , body ,sender_email,reciever,sender_password)
                    existing_user.account_status = True
                    db.commit()
                else:
                    login_url = 'https://themodern-groom.myshopify.com/account/login'
                    login_link = f'<a href="{login_url}">Click Here</a>'
                    body = f"You have been invited to an event. {login_link} to view the event details."
                    sender_password=password
                    reciever = attendee['email']
                    subject ='Wedding Invite'
                    send_email(subject , body ,sender_email,reciever,sender_password)
            return 'Email sent successfully', 200
        else:
            return "Data is missing or not in the correct format", 204
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500
    finally:
        db.close()
