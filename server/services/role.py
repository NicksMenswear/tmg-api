import uuid
from datetime import datetime
from typing import List, Dict

from server.database.database_manager import db
from server.database.models import Role, Event, Attendee
from server.models.role_model import RoleModel, CreateRoleModel, UpdateRoleModel
from server.models.event_model import EventTypeModel
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
    ],
    EventTypeModel.PROM: ["Attendee", "Attendee Parent or Chaperone"],
    EventTypeModel.OTHER: [
        "Attendee",
    ],
}


# noinspection PyMethodMayBeStatic
class RoleService:
    def __role_by_id(self, role_id: uuid.UUID) -> Role:
        role = Role.query.filter(Role.id == role_id).first()

        if not role:
            raise NotFoundError("Role not found.")

        return role

    def get_role_by_id(self, role_id: uuid.UUID) -> RoleModel:
        return RoleModel.from_orm(self.__role_by_id(role_id))

    def create_roles(self, create_roles: List[CreateRoleModel]) -> List[RoleModel]:
        roles = [Role(name=role.name, event_id=role.event_id, is_active=role.is_active) for role in create_roles]

        for role in roles:
            db.session.add(role)

        db.session.flush()

        return [RoleModel.from_orm(role) for role in roles]

    def create_role(self, create_role: CreateRoleModel) -> RoleModel:
        db_event = Event.query.filter(Event.id == create_role.event_id).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        existing_role = Role.query.filter(
            Role.name == create_role.name, Role.event_id == create_role.event_id, Role.is_active
        ).first()

        if existing_role:
            raise DuplicateError("Role already exists.")

        try:
            role = self.create_roles([create_role])[0]
        except Exception as e:
            raise ServiceError("Failed to create role.", e)

        return role

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

        num_attendees = Attendee.query.filter(Attendee.role_id == role_id).count()

        if num_attendees > 0:
            raise BadRequestError("Can't delete role associated to attendee")

        try:
            role.is_active = False
            role.updated_at = datetime.now()

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete role.", e)

    def get_roles_for_events(self, event_ids: List[uuid.UUID]) -> Dict[uuid.UUID, List[RoleModel]]:
        db_roles = Role.query.filter(Role.event_id.in_(event_ids), Role.is_active).order_by(Role.created_at.asc()).all()

        if not db_roles:
            return dict()

        roles = dict()

        for role in db_roles:
            if role.event_id not in roles:
                roles[role.event_id] = list()

            roles[role.event_id].append(RoleModel.from_orm(role))

        return roles

    def get_roles_for_event(self, event_id: uuid.UUID) -> List[RoleModel]:
        event = Event.query.filter(Event.id == event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        roles = self.get_roles_for_events([event_id])

        if not roles:
            return []

        return roles[event_id]
