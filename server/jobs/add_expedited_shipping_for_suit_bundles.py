import logging
import os

from server.services.user_service import UserService

logger = logging.getLogger(__name__)


def add_expedited_shipping_for_suit_bundles():
    logger.info(f"add_expedited_shipping_for_suit_bundles...")
    logger.info(f"STAGE: {os.environ.get('STAGE')}")

    user_service = UserService()

    print("hello world")
