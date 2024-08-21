import logging

from server.app import init_logging
from server.config import Config
from server.controllers.util import http

logger = logging.getLogger(__name__)

config = Config()


def lambda_handler_add_expedited_shipping_for_suit_bundles(event, context):
    init_logging(debug=True)
    # init_sentry()

    api_token = config.API_TOKEN
    endpoint = config.API_ENDPOINT_URL

    try:
        response = http(
            "POST",
            endpoint,
            json=None,
            headers={
                "Content-Type": "application/json",
                "X-Api-Access-Token": api_token,
            },
            timeout=600,
        )

        if response.status != 200:
            logger.error(f"Failed to add expedited shipping for suit bundles {response.status}: {response.json()}")
    except Exception as e:
        logger.exception(e)
