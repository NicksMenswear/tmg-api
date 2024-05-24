import logging
import uuid

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.role_model import UpdateRoleModel, CreateRoleModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create_role(role_data):
    role_service = FlaskApp.current().role_service

    role = role_service.create_role(CreateRoleModel(**role_data))

    return role.to_response(), 201


@hmac_verification
@error_handler
def get_role(role_id):
    role_service = FlaskApp.current().role_service

    role = role_service.get_role_by_id(uuid.UUID(role_id))

    return role.to_response(), 200


@hmac_verification
@error_handler
def update_role(role_id, role_data):
    role_service = FlaskApp.current().role_service

    role = role_service.update_role(uuid.UUID(role_id), UpdateRoleModel(**role_data))

    return role.to_response(), 200


@hmac_verification
@error_handler
def delete_role(role_id):
    role_service = FlaskApp.current().role_service

    role_service.delete_role(uuid.UUID(role_id))

    return jsonify({}), 204
