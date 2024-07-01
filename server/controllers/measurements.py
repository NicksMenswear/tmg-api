import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create(data):
    measurement_service = FlaskApp.current().measurement_service

    measurement_id = measurement_service.create_measurement(data)

    return {"id": measurement_id}, 201
