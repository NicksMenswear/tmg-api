import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService

logger = logging.getLogger(__name__)


@hmac_verification
def create_role(role_data):
    role_service = RoleService()
    event_service = EventService()
    look_service = LookService()

    if event_service.get_event_by_id(role_data["event_id"]) is None:
        return jsonify({"errors": "Event not found"}), 404

    if look_service.get_look_by_id(role_data["look_id"]) is None:
        return jsonify({"errors": "Look not found"}), 404

    try:
        role = role_service.create_role(**role_data)
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create role"}), 500

    return role.to_dict(), 201


@hmac_verification
def get_role(role_id, event_id):
    role_service = RoleService()

    role = role_service.get_role_by_id(role_id)

    if not role:
        return jsonify({"errors": "Role not found"}), 404

    return role.to_dict(), 200


@hmac_verification
def get_event_roles(event_id):
    role_service = RoleService()
    event_service = EventService()

    if not event_service.get_event_by_id(event_id):
        return jsonify({"errors": "Event not found"}), 404

    roles = role_service.get_roles_by_event_id(event_id)

    return jsonify([role.to_dict() for role in roles]), 200


@hmac_verification
def get_event_roles_with_look(event_id):
    event_service = EventService()
    event = event_service.get_event_by_id(event_id)

    if not event:
        return jsonify({"errors": "Event not found"}), 404

    role_service = RoleService()

    return role_service.get_event_roles_with_looks(event_id)


@hmac_verification
def list_roles():
    role_service = RoleService()

    return [role.to_dict() for role in role_service.get_all_roles()], 200


@hmac_verification
def update_role(role_data):
    role_service = RoleService()

    try:
        role = role_service.update_role(role_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to update role"}), 500

    return role.to_dict(), 200
