import logging

from server.controllers.util import token_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@token_verification
@error_handler
def e2e_clean_up():
    system_service = FlaskApp.current().system_service
    system_service.e2e_cleanup()

    return {}, 200
