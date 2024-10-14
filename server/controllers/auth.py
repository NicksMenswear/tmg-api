import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.services import NotFoundError

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def login(email):
    user_service = FlaskApp.current().user_service
    shopify_service = FlaskApp.current().shopify_service
    email_service = FlaskApp.current().email_service

    try:
        user = user_service.get_user_by_email(email)
    except NotFoundError as e:
        logger.warning(f"User not found for email: {email}")
        return None, 404

    shopify_customer = shopify_service.get_customer_by_email(email)

    if not shopify_customer:
        logger.warning(f"Shopify customer not found for email: {email}")
        return None, 404

    state = shopify_customer["state"]
    tags = shopify_customer["tags"]

    is_legacy = "legacy" in tags

    if is_legacy and state == "disabled":
        email_service.send_activation_email(user)
        return {"state": state, "is_legacy": is_legacy}, 200

    return {"state": state}, 200
