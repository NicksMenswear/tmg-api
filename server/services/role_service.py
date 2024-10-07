import uuid
from datetime import datetime
from typing import List, Dict

from sqlalchemy import select, func

from server.database.database_manager import db
from server.database.models import Role, Event, Attendee
from server.models.event_model import EventTypeModel
from server.models.role_model import RoleModel, CreateRoleModel, UpdateRoleModel
from server.services import ServiceError, NotFoundError, DuplicateError, BadRequestError

PREDEFINED_ROLES = {
    EventTypeModel.WEDDING: [
        "Bride",
        "Groom",
        "Groomsman",
        "Best Man",
        "Usher",
        "Father of the Groom",
        "Father of the Bride",
        "Officiant",
        "Other",
    ],
    EventTypeModel.PROM: ["Attendee", "Attendee Parent or Chaperone", "Other"],
    EventTypeModel.OTHER: ["Attendee", "Other"],
}


class RoleService:
    @staticmethod
    def __role_by_id(role_id: uuid.UUID) -> Role:
        role = db.session.execute(select(Role).where(Role.id == role_id)).scalar_one_or_none()

        if not role:
            raise NotFoundError("Role not found.")

        return role

    def get_role_by_id(self, role_id: uuid.UUID) -> RoleModel:
        return RoleModel.from_orm(self.__role_by_id(role_id))

    @staticmethod
    def create_roles(create_roles: List[CreateRoleModel]) -> List[RoleModel]:
        roles = [Role(name=role.name, event_id=role.event_id, is_active=role.is_active) for role in create_roles]

        for role in roles:
            db.session.add(role)

        db.session.flush()

        return [RoleModel.from_orm(role) for role in roles]

    def create_role(self, create_role: CreateRoleModel) -> RoleModel:
        db_event = db.session.execute(select(Event).where(Event.id == create_role.event_id)).scalar_one_or_none()

        if not db_event:
            raise NotFoundError("Event not found.")

        existing_role = db.session.execute(
            select(Role).where(Role.name == create_role.name, Role.event_id == create_role.event_id, Role.is_active)
        ).scalar_one_or_none()

        if existing_role:
            raise DuplicateError("Role already exists.")

        try:
            role = self.create_roles([create_role])[0]
        except Exception as e:
            raise ServiceError("Failed to create role.", e)

        return role

    def update_role(self, role_id: uuid.UUID, update_role: UpdateRoleModel) -> RoleModel:
        db_role = self.__role_by_id(role_id)

        existing_role_by_name = db.session.execute(
            select(Role).where(Role.name == update_role.name, Role.event_id == db_role.event_id)
        ).scalar_one_or_none()

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

        num_attendees = db.session.execute(select(func.count(Attendee.id)).where(Attendee.role_id == role_id)).scalar()

        if num_attendees > 0:
            raise BadRequestError("Can't delete role associated with attendee")

        try:
            role.is_active = False
            role.updated_at = datetime.now()

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete role.", e)

    @staticmethod
    def get_roles_for_events(event_ids: List[uuid.UUID]) -> Dict[uuid.UUID, List[RoleModel]]:
        db_roles = (
            db.session.execute(
                select(Role).where(Role.event_id.in_(event_ids), Role.is_active).order_by(Role.created_at.asc())
            )
            .scalars()
            .all()
        )

        if not db_roles:
            return dict()

        roles = dict()

        for role in db_roles:
            if role.event_id not in roles:
                roles[role.event_id] = list()

            roles[role.event_id].append(RoleModel.from_orm(role))

        return roles

    def get_roles_for_event(self, event_id: uuid.UUID) -> List[RoleModel]:
        event = db.session.execute(select(Event).where(Event.id == event_id)).scalar_one_or_none()

        if not event:
            raise NotFoundError("Event not found.")

        roles = self.get_roles_for_events([event_id])

        if not roles:
            return []

        return roles[event_id]
