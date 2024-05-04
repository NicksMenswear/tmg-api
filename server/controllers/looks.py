import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.look import LookService

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

    try:
        look = look_service.create_look(look_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 409
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
def get_events_for_look(look_id):
    look_service = LookService()

    events = look_service.get_events_for_look(look_id)

    return [event.to_dict() for event in events], 200


@hmac_verification
def update_look(look_id, look_data):
    look_service = LookService()

    try:
        look = look_service.update_look(look_id, look_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return look.to_dict(), 200


@hmac_verification
def delete_look(look_id):
    look_service = LookService()

    try:
        look_service.delete_look(look_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return jsonify({}), 204
