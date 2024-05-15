import logging
import os

from server.controllers.registration_email import send_email
from server.controllers.util import hmac_verification
from server.database.database_manager import db
from server.database.models import User
from server.services.shopify import ShopifyService

logger = logging.getLogger(__name__)


sender_email = os.getenv("sender_email")
password = os.getenv("sender_password")


@hmac_verification
def send_invite(invite_data):
    try:
        shopify_service = ShopifyService()

        if "data" in invite_data:
            for attendee in invite_data["data"]:
                existing_user = db.session.query(User).filter(User.email == attendee["email"]).first()
                if not existing_user.account_status:
                    activation_url = shopify_service.get_activation_url(existing_user.shopify_id)
                    logger.debug(activation_url)
                    activation_link = f'<a href="{activation_url}">Click Me</a>'
                    body = f"You have been invited to an event. Click the following link to activate your account: {activation_link}"
                    sender_password = password
                    reciever = attendee["email"]
                    subject = "Wedding Invite"
                    send_email(subject, body, sender_email, reciever, sender_password)
                    existing_user.account_status = True
                    db.session.commit()
                else:
                    login_url = "https://themodern-groom.myshopify.com/account/login"
                    login_link = f'<a href="{login_url}">Click Here</a>'
                    logger.debug(login_url)
                    body = f"You have been invited to an event. {login_link} to view the event details."
                    sender_password = password
                    reciever = attendee["email"]
                    subject = "Wedding Invite"
                    send_email(subject, body, sender_email, reciever, sender_password)
            return "Email sent successfully", 200
        else:
            return "Data is missing or not in the correct format", 204
    except Exception as e:
        db.session.rollback()
        logger.exception(e)
        return f"Internal Server Error : {e}", 500
