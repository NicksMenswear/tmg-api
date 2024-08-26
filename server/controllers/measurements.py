import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.measurement_model import CreateMeasurementsRequestModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create(data):
    measurement_service = FlaskApp.current().measurement_service

    measurement = measurement_service.create_measurement(CreateMeasurementsRequestModel(**data))

    return measurement.to_response(), 201
