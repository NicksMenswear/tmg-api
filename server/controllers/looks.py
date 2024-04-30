import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.look import LookService
from server.services.user import UserService

logger = logging.getLogger(__name__)


@hmac_verification
def get_look(look_id):
    look_service = LookService()

    look = look_service.get_look_by_id(look_id)

    if not look:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return look.to_dict(), 200


@hmac_verification
def create_look(look_data):
    look_service = LookService()
    user_service = UserService()

    user = user_service.get_user_by_email(look_data["email"])

    if not user:
        return jsonify({"errors": "User not found"}), 404

    try:
        del look_data["email"]
        enriched_look_data = {**look_data, "user_id": user.id}

        look = look_service.create_look(enriched_look_data)
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create look"}), 500

    return look.to_dict(), 201


@hmac_verification
def get_look_for_user(look_id, user_id):
    look_service = LookService()

    look = look_service.get_look_by_id_and_user(look_id, user_id)

    if not look:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return look.to_dict(), 200


@hmac_verification
def get_user_looks(user_id):
    look_service = LookService()

    looks = look_service.get_looks_for_user(user_id)

    return [look.to_dict() for look in looks]


@hmac_verification
def list_looks():
    look_service = LookService()

    return [look.to_dict() for look in look_service.get_all_looks()], 200


@hmac_verification
def update_look(look_data):
    look_service = LookService()

    try:
        look = look_service.update_look(look_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return look.to_dict(), 200
