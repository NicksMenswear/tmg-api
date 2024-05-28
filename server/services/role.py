import uuid
from datetime import datetime
from typing import List

from server.database.database_manager import db
from server.database.models import Role, Event
from server.models.role_model import RoleModel, CreateRoleModel, UpdateRoleModel
from server.services import ServiceError, NotFoundError, DuplicateError


# noinspection PyMethodMayBeStatic
class RoleService:
    def __role_by_id(self, role_id: uuid.UUID) -> Role:
        role = Role.query.filter(Role.id == role_id).first()

        if not role:
            raise NotFoundError("Role not found.")

        return role

    def get_role_by_id(self, role_id: uuid.UUID) -> RoleModel:
        return RoleModel.from_orm(self.__role_by_id(role_id))

    def create_role(self, create_role: CreateRoleModel) -> RoleModel:
        db_event = Event.query.filter(Event.id == create_role.event_id).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        existing_role = Role.query.filter(Role.name == create_role.name, Role.event_id == create_role.event_id).first()

        if existing_role:
            raise DuplicateError("Role already exists.")

        try:
            db_role = Role(name=create_role.name, event_id=create_role.event_id)

            db.session.add(db_role)
            db.session.commit()
            db.session.refresh(db_role)
        except Exception as e:
            raise ServiceError("Failed to create role.", e)

        return RoleModel.from_orm(db_role)

    def update_role(self, role_id: uuid.UUID, update_role: UpdateRoleModel) -> RoleModel:
        db_role = self.__role_by_id(role_id)

        existing_role_by_name = Role.query.filter(
            Role.name == update_role.name, Role.event_id == db_role.event_id
        ).first()

        if existing_role_by_name:
            raise DuplicateError("Role with this name already exists.")

        try:
            db_role.name = update_role.name
            db_role.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(db_role)
        except Exception as e:
            raise ServiceError("Failed to update role.", e)

        return RoleModel.from_orm(db_role)

    def delete_role(self, role_id: uuid.UUID) -> None:
        role = self.__role_by_id(role_id)

        try:
            db.session.delete(role)
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete role.", e)

    def get_roles_for_event(self, event_id: uuid.UUID) -> List[RoleModel]:
        event = Event.query.filter(Event.id == event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        roles = Role.query.filter(Role.event_id == event_id).order_by(Role.created_at.asc()).all()

        return [RoleModel.from_orm(role) for role in roles]
