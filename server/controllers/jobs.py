import logging

from server.controllers.util import token_verification

logger = logging.getLogger(__name__)


@token_verification
def hello_world():
    logger.info("Hello world executed")

    return {}, 200
