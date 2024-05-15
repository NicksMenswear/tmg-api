import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.user import UserService

logger = logging.getLogger(__name__)


@hmac_verification
def create_user(user_data):
    user_service = UserService()

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
    user_service = UserService()

    try:
        user = user_service.get_user_by_email(email)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404

    return user.to_dict(), 200


@hmac_verification
def get_user_events(user_id):
    user_service = UserService()

    events = user_service.get_user_events(user_id)

    return [event.to_dict() for event in events], 200


@hmac_verification
def get_user_invites(user_id):
    user_service = UserService()

    events = user_service.get_user_invites(user_id)

    return [event.to_dict() for event in events], 200


@hmac_verification
def get_user_looks(user_id):
    user_service = UserService()

    looks = user_service.get_user_looks(user_id)

    return [look.to_dict() for look in looks]


@hmac_verification
def get_user_discounts(user_id, event_id=None):
    user_service = UserService()

    discounts = user_service.get_user_discounts(user_id, event_id)

    return [discount.to_dict() for discount in discounts], 200


@hmac_verification
def update_user(user_id, user_data):
    user_service = UserService()

    try:
        user = user_service.update_user(user_id, user_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to update user."}), 500

    return user.to_dict(), 200
