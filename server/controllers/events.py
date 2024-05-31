import logging
import uuid

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.event_model import CreateEventModel, UpdateEventModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_event_by_id(event_id, enriched=False):
    event_service = FlaskApp.current().event_service

    event = event_service.get_event_by_id(uuid.UUID(event_id), enriched=enriched)

    if enriched:
        return event.to_enriched_response(), 200

    return event.to_response(), 200


@hmac_verification
@error_handler
def create_event(create_event):
    event_service = FlaskApp.current().event_service

    event = event_service.create_event(CreateEventModel(**create_event))

    return event.to_response(), 201


@hmac_verification
@error_handler
def update_event(event_id, update_event):
    event_service = FlaskApp.current().event_service

    event = event_service.update_event(uuid.UUID(event_id), UpdateEventModel(**update_event))

    return event.to_response(), 200


@hmac_verification
@error_handler
def delete_event(event_id):
    event_service = FlaskApp.current().event_service

    event_service.delete_event(uuid.UUID(event_id))

    return None, 204


@hmac_verification
@error_handler
def get_event_roles(event_id):
    role_service = FlaskApp.current().role_service

    roles = role_service.get_roles_for_event(uuid.UUID(event_id))

    return [role.to_response() for role in roles], 200


@hmac_verification
@error_handler
def get_event_attendees(event_id):
    attendee_service = FlaskApp.current().attendee_service

    attendees = attendee_service.get_attendees_for_event(uuid.UUID(event_id))

    return [attendee.to_response() for attendee in attendees], 200
