import logging

from server.controllers.util import error_handler, token_verification
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@token_verification
@error_handler
def create(user_id, data):
    sizing_service = FlaskApp.current().sizing_service

    sizing_id = sizing_service.create(user_id, data)

    return {"id": sizing_id}, 201
