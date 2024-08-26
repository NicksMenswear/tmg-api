import logging

from server.config import Config

from server.app import init_sentry
from server.controllers.util import http
from server.logs import init_logging

logger = logging.getLogger(__name__)

config = Config()


def lambda_handler_hello_world(event, context):
    init_logging("job_hello_world", debug=True)
    init_sentry()

    api_token = config.API_TOKEN
    endpoint = f"{config.API_ENDPOINT_URL}/jobs/hello-world"

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
            logger.error(f"Failed to execute hello world {response.status}: {response.json()}")
    except Exception as e:
        logger.exception(e)
