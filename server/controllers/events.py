import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.database.database_manager import db
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.event import EventService
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
def create_event(event):
    event_service = EventService()

    try:
        event = event_service.create_event(**event)
    except NotFoundError as e:
        logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except DuplicateError as e:
        logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return event.to_dict(), 201


@hmac_verification
def list_events(email):
    event_service = EventService()

    try:
        events = event_service.get_events_with_looks_by_user_email(email)
    except NotFoundError as e:
        logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404

    return events, 200


@hmac_verification
def list_events_attendees(email):
    event_service = EventService()

    try:
        events = event_service.get_events_with_attendees_by_user_email(email)
    except NotFoundError as e:
        logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404

    return events, 200


@hmac_verification
def update_event(event):
    event_service = EventService()

    try:
        event = event_service.update_event(**event)
    except NotFoundError as e:
        logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return event.to_dict(), 200


@hmac_verification
def soft_delete_event(event):
    event_service = EventService()

    try:
        event_service.soft_delete_event(**event)
    except NotFoundError as e:
        logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return None, 204
