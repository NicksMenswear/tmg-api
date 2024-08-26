import logging

from server.controllers.util import token_verification, log_request

logger = logging.getLogger(__name__)


@token_verification
@log_request
def hello_world():
    logger.info("Hello world executed")

    return {}, 200
