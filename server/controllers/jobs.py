import logging

from server.controllers.util import token_verification

logger = logging.getLogger(__name__)


@token_verification
def e2e_clean_up():
    logger.info("e2e clean up")

    return {}, 200
