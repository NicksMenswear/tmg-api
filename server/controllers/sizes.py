import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.size_model import CreateSizeRequestModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create(data):
    sizing_service = FlaskApp.current().size_service

    sizing_model = sizing_service.create_size(CreateSizeRequestModel(**data))

    return {"id": sizing_model.id}, 201
