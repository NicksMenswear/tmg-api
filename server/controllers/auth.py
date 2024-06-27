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

    try:
        user = user_service.get_user_by_email(email)
    except NotFoundError as e:
        logger.warning(f"User not found by email {email} on login")
        user = None

    try:
        shopify_customer = shopify_service.get_customer_by_email(email)
    except NotFoundError as e:
        logger.warning(f"Shopify customer not found by email {email} on login")
        shopify_customer = None

    # TODO: Refactor this weird response

    if shopify_customer:
        state = shopify_customer["state"]
        tags = shopify_customer["tags"]
        is_legacy = "legacy" in tags.split(",") if tags else False

        if user:
            return {"tmg_state": user.account_status, "shopify_state": state, "is_legacy": is_legacy}, 200
        else:
            return {"tmg_state": "User not found", "shopify_state": state, "is_legacy": is_legacy}, 200
    else:
        if user:
            return {"tmg_state": user.account_status, "shopify_state": "User not found", "is_legacy": False}, 200
        else:
            return {"tmg_state": "User not found", "shopify_state": "User not found", "is_legacy": False}, 404
