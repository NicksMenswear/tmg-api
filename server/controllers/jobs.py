import logging

from server.controllers.util import token_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@token_verification
@error_handler
def e2e_clean_up():
    e2e_cleanup_service = FlaskApp.current().e2e_cleanup_service
    e2e_cleanup_service.cleanup()

    return {}, 200
