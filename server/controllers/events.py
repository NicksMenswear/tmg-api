from urllib.parse import unquote

from flask import current_app as app, jsonify

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session, session_factory
from server.database.models import Event, User, Look, Role, Attendee
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.event import EventService

db = get_database_session()


@hmac_verification()
def create_event(event):
    event_service = EventService(session_factory())

    try:
        event = event_service.create_event(**event)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except DuplicateError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return event.to_dict(), 201


@hmac_verification()
def list_events(email):
    event_service = EventService(session_factory())

    try:
        events = event_service.get_events_with_looks_by_user_email(email)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404

    return events, 200


@hmac_verification()
def list_events_attendees(email):
    email = unquote(email)

    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return "User not found", 200
        formatted_data = []
        attendees = db.query(Attendee).filter(Attendee.attendee_id == user.id).all()
        for attendee in attendees:
            event = db.query(Event).filter(Event.id == attendee.event_id, Event.is_active == True).first()
            if event is None:
                continue
            role = db.query(Role).filter(Role.id == attendee.role).first()

            if role:
                look = db.query(Look).filter(Look.id == role.look_id).first()

                if look is None:
                    look_data = {}
                else:
                    look_data = {
                        "id": look.id,
                        "look_name": look.look_name,
                        "product_specs": look.product_specs,
                        "product_final_image": look.product_final_image,
                    }
                data = {
                    "event_id": event.id,
                    "event_name": event.event_name,
                    "event_date": str(event.event_date),
                    "user_id": str(event.user_id),
                    "look_data": look_data,
                }
                formatted_data.append(data)
            else:
                look_data = {}
                data = {
                    "event_id": event.id,
                    "event_name": event.event_name,
                    "event_date": str(event.event_date),
                    "user_id": str(event.user_id),
                    "look_data": look_data,
                }
                formatted_data.append(data)

        return formatted_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Internal Server Error : {e}", 500


@hmac_verification()
def update_event(event):
    event_service = EventService(session_factory())

    try:
        event = event_service.update_event(**event)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return event.to_dict(), 200


@hmac_verification()
def soft_delete_event(event):
    event_service = EventService(session_factory())

    try:
        event_service.soft_delete_event(**event)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return None, 204
