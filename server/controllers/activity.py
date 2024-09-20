import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def generic(data):
    activity_service = FlaskApp.current().activity_service

    response = activity_service.generic(**data)

    return response, 200
