import logging

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create_role(role_data):
    role_service = FlaskApp.current().role_service

    role = role_service.create_role(role_data)

    return role.to_dict(), 201


@hmac_verification
@error_handler
def get_role(role_id):
    role_service = FlaskApp.current().role_service

    role = role_service.get_role_by_id(role_id)

    if not role:
        return jsonify({"errors": "Role not found"}), 404

    role = role_service.get_role_by_id(role_id)

    return role.to_dict(), 200


@hmac_verification
@error_handler
def update_role(role_id, role_data):
    role_service = FlaskApp.current().role_service

    role = role_service.update_role(role_id, role_data)

    return role.to_dict(), 200


@hmac_verification
@error_handler
def delete_role(role_id):
    role_service = FlaskApp.current().role_service

    role_service.delete_role(role_id)

    return "", 204
