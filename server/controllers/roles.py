import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.flask_app import FlaskApp
from server.services import ServiceError, DuplicateError, NotFoundError

logger = logging.getLogger(__name__)


@hmac_verification
def create_role(role_data):
    role_service = FlaskApp.current().role_service

    try:
        role = role_service.create_role(role_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create role"}), 500

    return role.to_dict(), 201


@hmac_verification
def get_role(role_id):
    role_service = FlaskApp.current().role_service

    role = role_service.get_role_by_id(role_id)

    if not role:
        return jsonify({"errors": "Role not found"}), 404

    try:
        role = role_service.get_role_by_id(role_id)
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to get role"}), 500

    return role.to_dict(), 200


@hmac_verification
def update_role(role_id, role_data):
    role_service = FlaskApp.current().role_service

    try:
        role = role_service.update_role(role_id, role_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to update role"}), 500

    return role.to_dict(), 200


@hmac_verification
def delete_role(role_id):
    role_service = FlaskApp.current().role_service

    try:
        role_service.delete_role(role_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to delete role"}), 500

    return "", 204
