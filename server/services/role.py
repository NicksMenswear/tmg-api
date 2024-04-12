import uuid

from server.database.models import Role, Look
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.base import BaseService


class RoleService(BaseService):
    def get_all_roles(self):
        with self.session_factory() as db:
            return db.query(Role).all()

    def get_role_by_name(self, role_name):
        with self.session_factory() as db:
            return db.query(Role).filter(Role.role_name == role_name).first()

    def create_role(self, **role_data):
        with self.session_factory() as db:
            role = db.query(Role).filter(Role.role_name == role_data["role_name"]).first()

            if role:
                raise DuplicateError("Role already exists with this name.")

            try:
                role = Role(
                    id=uuid.uuid4(),
                    role_name=role_data["role_name"],
                    event_id=role_data["event_id"],
                    look_id=role_data["look_id"],
                )

                db.add(role)
                db.commit()
                db.refresh(role)
            except Exception as e:
                raise ServiceError("Failed to create role.", e)

            return role

    def get_role_by_id(self, role_id):
        with self.session_factory() as db:
            return db.query(Role).filter(Role.id == role_id).first()

    def get_roles_by_event_id(self, event_id):
        with self.session_factory() as db:
            return db.query(Role).filter(Role.event_id == event_id).all()

    def get_event_roles_with_looks(self, event_id):
        with self.session_factory() as db:
            roles = db.query(Role).filter(Role.event_id == event_id).all()

            formatted_role_data = []
            formatted_look_data = []
            for role in roles:
                look = db.query(Look).filter(Look.id == role.look_id).first()
                data = {
                    "role_id": role.id,
                    "role_name": role.role_name,
                    "event_id": role.event_id,
                    "look_data": {"look_id": look.id, "look_name": look.look_name},
                }
                formatted_role_data.append(data)

            look_details = db.query(Look).filter(Look.event_id == event_id).all()

            for look in look_details:
                look_data = {"look_id": look.id, "look_name": look.look_name}
                formatted_look_data.append(look_data)

            return {"role_details": formatted_role_data, "all_looks": formatted_look_data}

    def update_role(self, role_data):
        with self.session_factory() as db:
            role = db.query(Role).filter(Role.role_name == role_data["role_name"]).first()

            if not role:
                raise NotFoundError("Role not found.")

            try:
                role.role_name = role_data["new_role_name"]
                role.look_id = role_data["look_id"]
                db.commit()
                db.refresh(role)
            except Exception as e:
                raise ServiceError("Failed to update role.", e)

            return role
