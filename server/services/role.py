import uuid

from server.database.models import Role
from server.services import ServiceError
from server.services.base import BaseService


class RoleService(BaseService):
    def get_all_roles(self):
        with self.session_factory() as db:
            return db.query(Role).all()

    def create_role(self, **role_data):
        with self.session_factory() as db:
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
