import logging
import os

from server.services.email_service import EmailService
from server.services.integrations.shopify_service import ShopifyService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


def add_expedited_shipping_for_suit_bundles():
    try:
        logger.info(f"add_expedited_shipping_for_suit_bundles...")
        logger.info(f"STAGE: {os.environ.get('STAGE')}")

        print("hello world")

        shopify_service = ShopifyService()
        email_service = EmailService(shopify_service)
        user_service = UserService(shopify_service, email_service)

        print(user_service.get_user_by_email("zinovii+01@themoderngroom.com"))
    except Exception as e:
        logger.error(f"Error adding expedited shipping for suit bundles: {e}")
        raise e
