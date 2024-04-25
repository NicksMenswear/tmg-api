import uuid

from server.database.database_manager import db
from server.database.models import Role, Look
from server.services import ServiceError, NotFoundError
from server.services.base import BaseService


class RoleService(BaseService):
    def get_all_roles(self):
        return Role.query.all()

    def get_role_by_name(self, role_name):
        return Role.query.filter(Role.role_name == role_name).first()

    def create_role(self, **role_data):
        # role = Role.query.filter(Role.role_name == role_data["role_name"], Role.event_id == role_data["event_id"]).first()
        #
        # if role:
        #     raise DuplicateError("Role already exists with this name.")

        try:
            role = Role(
                id=uuid.uuid4(),
                role_name=role_data["role_name"],
                event_id=role_data["event_id"],
                look_id=role_data["look_id"],
            )

            db.session.add(role)
            db.session.commit()
            db.session.refresh(role)
        except Exception as e:
            raise ServiceError("Failed to create role.", e)

        return role

    def get_role_by_id(self, role_id):
        return Role.query.filter(Role.id == role_id).first()

    def get_roles_by_event_id(self, event_id):
        return Role.query.filter(Role.event_id == event_id).all()

    def get_role_by_look_id_and_event_id(self, look_id, event_id):
        return Role.query.filter(Role.look_id == look_id, Role.event_id == event_id).first()

    def get_event_roles_with_looks(self, event_id):
        roles = Role.query.filter(Role.event_id == event_id).all()

        formatted_role_data = []
        formatted_look_data = []
        for role in roles:
            look = Look.query.filter(Look.id == role.look_id).first()
            data = {
                "role_id": role.id,
                "role_name": role.role_name,
                "event_id": role.event_id,
                "look_data": {"look_id": look.id, "look_name": look.look_name},
            }
            formatted_role_data.append(data)

        look_details = Look.query.filter(Look.event_id == event_id).all()

        for look in look_details:
            look_data = {"look_id": look.id, "look_name": look.look_name}
            formatted_look_data.append(look_data)

        return {"role_details": formatted_role_data, "all_looks": formatted_look_data}

    def update_role(self, role_data):
        role = Role.query.filter(Role.role_name == role_data["role_name"]).first()

        if not role:
            raise NotFoundError("Role not found.")

        try:
            role.role_name = role_data["new_role_name"]
            role.look_id = role_data["look_id"]
            db.session.commit()
            db.session.refresh(role)
        except Exception as e:
            raise ServiceError("Failed to update role.", e)

        return role
