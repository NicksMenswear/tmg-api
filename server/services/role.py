import uuid

from server.database.database_manager import db
from server.database.models import Role, Event
from server.services import ServiceError, NotFoundError, DuplicateError


class RoleService:
    def create_role(self, role_data):
        event = Event.query.filter(Event.id == role_data["event_id"]).first()

        if not event:
            raise NotFoundError("Event not found.")

        existing_role = Role.query.filter(
            Role.role_name == role_data["role_name"], Role.event_id == role_data["event_id"]
        ).first()

        if existing_role:
            raise DuplicateError("Role already exists.")

        try:
            role = Role(id=uuid.uuid4(), role_name=role_data["role_name"], event_id=role_data["event_id"])

            db.session.add(role)
            db.session.commit()
            db.session.refresh(role)
        except Exception as e:
            raise ServiceError("Failed to create role.", e)

        return role

    def get_role_by_id(self, role_id):
        return Role.query.filter(Role.id == role_id).first()

    def update_role(self, role_id, role_data):
        role = Role.query.filter(Role.id == role_id).first()

        if not role:
            raise NotFoundError("Role not found.")

        existing_role_by_name = Role.query.filter(
            Role.role_name == role_data["role_name"], Role.event_id == role.event_id
        ).first()

        if existing_role_by_name:
            raise DuplicateError("Role with this name already exists.")

        try:
            role.role_name = role_data["role_name"]

            db.session.commit()
            db.session.refresh(role)
        except Exception as e:
            raise ServiceError("Failed to update role.", e)

        return role

    def delete_role(self, role_id):
        role = Role.query.filter(Role.id == role_id).first()

        if not role:
            raise NotFoundError("Role not found.")

        try:
            db.session.delete(role)
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete role.", e)
