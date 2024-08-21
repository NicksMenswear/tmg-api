import logging
import os

logger = logging.getLogger(__name__)


def add_expedited_shipping_for_suit_bundles():
    try:
        logger.info(f"add_expedited_shipping_for_suit_bundles...")
        logger.info(f"STAGE: {os.environ.get('STAGE')}")

        print("hello world")
    except Exception as e:
        logger.error(f"Error adding expedited shipping for suit bundles: {e}")
        raise e
