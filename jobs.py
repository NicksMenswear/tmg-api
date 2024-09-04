import logging

from server.app import init_sentry
from server.config import Config
from server.controllers.util import http
from server.logs import init_logging

logger = logging.getLogger(__name__)

config = Config()


def lambda_handler_e2e_clean_up(event, context):
    init_logging("job_e2e_clean_up", debug=True)
    init_sentry()

    api_token = config.API_TOKEN
    endpoint = f"{config.API_ENDPOINT_URL}/jobs/system/e2e-clean-up"

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
            logger.error(f"Failed to execute e2e clean up job {response.status}: {response.json()}")
    except Exception as e:
        logger.exception(e)
