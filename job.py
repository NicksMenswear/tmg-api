import logging
import os

from server.app import init_logging
from server.controllers.util import http

logger = logging.getLogger(__name__)


def lambda_handler_add_expedited_shipping_for_suit_bundles(event, context):
    init_logging(debug=True)
    # init_sentry()

    stage = os.getenv("STAGE", "dev")
    api_key = os.getenv("API_KEY", "123")
    endpoint = os.getenv("API_URL", f"https://api.{stage}.tmgcorp.net/jobs/add-expedited-shipping-for-suit-bundles")

    try:
        response = http(
            "POST",
            endpoint,
            json=None,
            headers={
                "Content-Type": "application/json",
                "X-Api-Access-Token": api_key,
            },
            timeout=600,
        )

        if response.status != 200:
            logger.error(f"Failed to add expedited shipping for suit bundles {response.status}: {response.text}")
    except Exception as e:
        logger.exception(e)
