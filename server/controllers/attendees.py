import os

from flask import current_app as app
from flask import jsonify

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session, session_factory
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.attendee import AttendeeService

sender_email = os.getenv("sender_email")
password = os.getenv("sender_password")
db = get_database_session()


@hmac_verification()
def add_attendee(attendee_data):
    attendee_service = AttendeeService(session_factory())

    try:
        attendee = attendee_service.create_attendee(**attendee_data)
    except DuplicateError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": DuplicateError.MESSAGE}), 409
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to create attendee"}), 500

    return attendee.to_dict(), 201


@hmac_verification()
def get_attendee_event(email, event_id):
    attendee_service = AttendeeService(session_factory())

    try:
        event = attendee_service.get_attendee_event(email, event_id)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to get attendee's event"}), 500

    return event.to_dict(), 200


@hmac_verification()
def update_attendee(attendee_data):
    attendee_service = AttendeeService(session_factory())

    try:
        attendee = attendee_service.update_attendee(**attendee_data)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to get attendee"}), 500

    return attendee.to_dict(), 200


@hmac_verification()
def get_attendees_by_eventid(event_id):
    attendee_service = AttendeeService(session_factory())

    try:
        attendees = attendee_service.get_attendees_for_event_by_id(event_id)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404

    return attendees, 200


@hmac_verification()
def soft_delete_attendee(attendee_data):
    attendee_service = AttendeeService(session_factory())

    try:
        attendee_service.soft_delete_attendee(**attendee_data)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return None, 204
