import logging
import os

logger = logging.getLogger(__name__)


def sync_users_from_legacy_db():
    logger.info(f"Running sync_users_from_legacy_db job...")
    logger.info(f"STAGE: {os.environ.get('STAGE')}")
    print("hello world")
