import logging

from server.controllers.util import error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@error_handler
def store(data):
    sizing_service = FlaskApp.current().sizing_service

    sizing_id = sizing_service.store(data)

    return {"id": sizing_id}, 201
