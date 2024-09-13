import logging

from aws_lambda_powertools.logging import correlation_paths

from server.app import init_sentry
from server.config import Config
from server.controllers.util import http
from server.logs import init_logging, powerlogger

logger = logging.getLogger(__name__)

config = Config()

init_logging("job_e2e_clean_up", debug=True)
init_sentry()


@powerlogger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def lambda_handler_e2e_clean_up(event, context):
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
