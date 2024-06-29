import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create(data):
    sizing_service = FlaskApp.current().size_service

    sizing_id = sizing_service.create(data)

    return {"id": sizing_id}, 201
