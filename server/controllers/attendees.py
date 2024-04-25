import logging
import os

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.attendee import AttendeeService

logger = logging.getLogger(__name__)

sender_email = os.getenv("sender_email")
password = os.getenv("sender_password")


@hmac_verification
def add_attendee(attendee_data):
    attendee_service = AttendeeService()

    try:
        attendee = attendee_service.create_attendee(**attendee_data)
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": DuplicateError.MESSAGE}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create attendee"}), 500

    return attendee.to_dict(), 201


@hmac_verification
def get_attendee_event(email, event_id):
    attendee_service = AttendeeService()

    try:
        event = attendee_service.get_attendee_event(email, event_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to get attendee's event"}), 500

    return event.to_dict(), 200


@hmac_verification
def update_attendee(attendee_data):
    attendee_service = AttendeeService()

    try:
        attendee = attendee_service.update_attendee(**attendee_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to get attendee"}), 500

    return attendee.to_dict(), 200


@hmac_verification
def get_attendees_by_eventid(event_id):
    attendee_service = AttendeeService()

    try:
        attendees = attendee_service.get_attendees_for_event_by_id(event_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404

    return attendees, 200


@hmac_verification
def soft_delete_attendee(attendee_data):
    attendee_service = AttendeeService()

    try:
        attendee_service.soft_delete_attendee(**attendee_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return None, 204
