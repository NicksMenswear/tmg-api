import uuid

from flask import jsonify
from flask import current_app as app

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session, session_factory
from server.database.models import Look, User, Role, Attendee, Event
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.look import LookService
from server.services.user import UserService

db = get_database_session()


@hmac_verification()
def create_look(look_data):
    session = session_factory()

    look_service = LookService(session)
    user_service = UserService(session)

    user = user_service.get_user_by_email(look_data["email"])

    if not user:
        return jsonify({"errors": "User not found"}), 404

    try:
        del look_data["email"]
        enriched_look_data = {**look_data, "user_id": user.id}

        look = look_service.create_look(**enriched_look_data)
    except DuplicateError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to create look"}), 500

    return look.to_dict(), 201


@hmac_verification()
def get_look(look_id, user_id):
    look_service = LookService(session_factory())

    look = look_service.get_look_by_id_and_user(look_id, user_id)

    if not look:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return look.to_dict(), 200


@hmac_verification()
def get_user_looks(user_id):
    look_service = LookService(session_factory())

    looks = look_service.get_looks_for_user(user_id)

    return [look.to_dict() for look in looks]


@hmac_verification()
def list_looks():
    look_service = LookService(session_factory())

    return [look.to_dict() for look in look_service.get_all_looks()], 200


@hmac_verification()
def update_look(look_data):
    look_service = LookService(session_factory())

    try:
        look = look_service.update_look(**look_data)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return look.to_dict(), 200
