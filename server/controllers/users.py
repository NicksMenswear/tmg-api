import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.flask_app import FlaskApp
from server.services import ServiceError, DuplicateError, NotFoundError

logger = logging.getLogger(__name__)


@hmac_verification
def create_user(user_data):
    user_service = FlaskApp.current().user_service

    try:
        user = user_service.create_user(user_data)
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": DuplicateError.MESSAGE}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create user"}), 500

    return user.to_dict(), 201


@hmac_verification
def get_user_by_email(email):
    user_service = FlaskApp.current().user_service

    user = user_service.get_user_by_email(email)

    if not user:
        return jsonify({"errors": "User not found"}), 404

    return user.to_dict(), 200


@hmac_verification
def get_user_events(user_id, status=None):
    user_service = FlaskApp.current().user_service

    events = user_service.get_user_events(user_id, status=status)

    return events, 200


@hmac_verification
def get_user_looks(user_id):
    user_service = FlaskApp.current().user_service

    looks = user_service.get_user_looks(user_id)

    return [look.to_dict() for look in looks]


@hmac_verification
def update_user(user_id, user_data):
    user_service = FlaskApp.current().user_service

    try:
        user = user_service.update_user(user_id, user_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to update user."}), 500

    return user.to_dict(), 200
