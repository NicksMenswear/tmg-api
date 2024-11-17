import logging
import uuid

from flask import request

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.look_model import CreateLookModel, UpdateLookModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_look_by_id(look_id):
    look_service = FlaskApp.current().look_service

    look = look_service.get_look_by_id(uuid.UUID(look_id))

    return look.to_response(), 200


@hmac_verification
@error_handler
def create_look(create_look):
    look_service = FlaskApp.current().look_service

    look = look_service.create_look(CreateLookModel(**create_look))

    return look.to_response(), 201


@hmac_verification
@error_handler
def get_events_for_look(look_id):
    event_service = FlaskApp.current().event_service

    events = event_service.get_events_for_look(uuid.UUID(look_id))

    return [event.to_response() for event in events], 200


@hmac_verification
@error_handler
def update_look(look_id, update_look):
    look_service = FlaskApp.current().look_service

    look = look_service.update_look(uuid.UUID(look_id), UpdateLookModel(**update_look))

    return look.to_response(), 200


@hmac_verification
@error_handler
def delete_look(look_id):
    look_service = FlaskApp.current().look_service

    look_service.delete_look(uuid.UUID(look_id))

    return None, 204
