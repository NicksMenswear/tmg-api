import logging

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_event(event_id, enriched=False):
    event_service = FlaskApp.current().event_service

    if not enriched:
        event = event_service.get_event_by_id(event_id)

        if not event:
            return jsonify({}), 404

        return event.to_dict(), 200
    else:
        return event_service.get_enriched_event_by_id(event_id), 200


@hmac_verification
@error_handler
def create_event(event):
    event_service = FlaskApp.current().event_service

    event = event_service.create_event(event)

    return event.to_dict(), 201


@hmac_verification
@error_handler
def update_event(event_id, event_data):
    event_service = FlaskApp.current().event_service

    event = event_service.update_event(event_id, event_data)

    return event.to_dict(), 200


@hmac_verification
@error_handler
def soft_delete_event(event_id):
    event_service = FlaskApp.current().event_service

    event_service.soft_delete_event(event_id)

    return None, 204


@hmac_verification
@error_handler
def get_event_roles(event_id):
    event_service = FlaskApp.current().event_service

    roles = event_service.get_roles_for_event(event_id)

    return jsonify([role.to_dict() for role in roles]), 200


@hmac_verification
@error_handler
def get_event_attendees(event_id):
    event_service = FlaskApp.current().event_service

    attendees = event_service.get_attendees_for_event(event_id)

    return attendees, 200
