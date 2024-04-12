from flask import current_app as app, jsonify

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session, session_factory
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.event import EventService
from server.services.look import LookService
from server.services.role import RoleService

db = get_database_session()


@hmac_verification()
def create_role(role_data):
    session = session_factory()

    role_service = RoleService(session)
    event_service = EventService(session)
    look_service = LookService(session)

    if event_service.get_event_by_id(role_data["event_id"]) is None:
        return jsonify({"errors": "Event not found"}), 404

    if look_service.get_look_by_id(role_data["look_id"]) is None:
        return jsonify({"errors": "Look not found"}), 404

    try:
        role = role_service.create_role(**role_data)
    except DuplicateError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to create role"}), 500

    return role.to_dict(), 201


@hmac_verification()
def get_role(role_id, event_id):
    role_service = RoleService(session_factory())

    role = role_service.get_role_by_id(role_id)

    if not role:
        return jsonify({"errors": "Role not found"}), 404

    return role.to_dict(), 200


@hmac_verification()
def get_event_roles(event_id):
    session = session_factory()

    role_service = RoleService(session)
    event_service = EventService(session)

    if not event_service.get_event_by_id(event_id):
        return jsonify({"errors": "Event not found"}), 404

    roles = role_service.get_roles_by_event_id(event_id)

    return jsonify([role.to_dict() for role in roles]), 200


@hmac_verification()
def get_event_roles_with_look(event_id):
    session = session_factory()

    event_service = EventService(session)
    event = event_service.get_event_by_id(event_id)

    if not event:
        return jsonify({"errors": "Event not found"}), 404

    role_service = RoleService(session)

    return role_service.get_event_roles_with_looks(event_id)


@hmac_verification()
def list_roles():
    role_service = RoleService(session_factory())

    return [role.to_dict() for role in role_service.get_all_roles()], 200


@hmac_verification()
def update_role(role_data):
    role_service = RoleService(session_factory())

    try:
        role = role_service.update_role(role_data)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": "Failed to update role"}), 500

    return role.to_dict(), 200
