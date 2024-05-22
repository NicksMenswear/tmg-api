import logging

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.services import NotFoundError

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_look(look_id):
    look_service = FlaskApp.current().look_service

    look = look_service.get_look_by_id(look_id)

    if not look:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return look.to_dict(), 200


@hmac_verification
@error_handler
def create_look(look_data):
    look_service = FlaskApp.current().look_service

    look = look_service.create_look(look_data)

    return look.to_dict(), 201


@hmac_verification
@error_handler
def get_events_for_look(look_id):
    look_service = FlaskApp.current().look_service

    events = look_service.get_events_for_look(look_id)

    return [event.to_dict() for event in events], 200


@hmac_verification
@error_handler
def update_look(look_id, look_data):
    look_service = FlaskApp.current().look_service

    look = look_service.update_look(look_id, look_data)

    return look.to_dict(), 200


@hmac_verification
@error_handler
def delete_look(look_id):
    look_service = FlaskApp.current().look_service

    look_service.delete_look(look_id)

    return jsonify({}), 204
