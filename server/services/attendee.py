import uuid
from datetime import datetime
from typing import List, Dict, Optional

from server.database.database_manager import db
from server.database.models import Attendee, Event, User, Role, Look
from server.models.attendee_model import (
    AttendeeModel,
    CreateAttendeeModel,
    UpdateAttendeeModel,
    EnrichedAttendeeModel,
    AttendeeUserModel,
)
from server.models.look_model import LookModel
from server.models.role_model import RoleModel
from server.models.user_model import CreateUserModel
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.shopify import AbstractShopifyService
from server.services.user import UserService


# noinspection PyMethodMayBeStatic
class AttendeeService:
    def __init__(self, shopify_service: AbstractShopifyService, user_service: UserService):
        self.shopify_service = shopify_service
        self.user_service = user_service

    def get_attendee_by_id(self, attendee_id: uuid.UUID, is_active: bool = True) -> AttendeeModel:
        attendee = Attendee.query.filter(Attendee.id == attendee_id, Attendee.is_active == is_active).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        return AttendeeModel.from_orm(attendee)

    def get_attendees_for_events(
        self, event_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> Dict[uuid.UUID, List[EnrichedAttendeeModel]]:
        query = (
            db.session.query(Attendee, User, Role, Look)
            .join(User, User.id == Attendee.user_id)
            .outerjoin(Role, Attendee.role_id == Role.id)
            .outerjoin(Look, Attendee.look_id == Look.id)
            .filter(Attendee.event_id.in_(event_ids), Attendee.is_active)
            .order_by(Attendee.created_at.asc())
        )

        if user_id is not None:
            query = query.filter(Attendee.user_id == user_id)

        db_attendees = query.all()

        if not db_attendees:
            return dict()

        attendees = dict()

        for attendee, user, role, look in db_attendees:
            if attendee.event_id not in attendees:
                attendees[attendee.event_id] = list()

            attendees[attendee.event_id].append(
                EnrichedAttendeeModel(
                    id=attendee.id,
                    user_id=attendee.user_id,
                    event_id=attendee.event_id,
                    style=attendee.style,
                    invite=attendee.invite,
                    pay=attendee.pay,
                    size=attendee.size,
                    ship=attendee.ship,
                    role_id=attendee.role_id,
                    look_id=attendee.look_id,
                    role=RoleModel.from_orm(role) if role else None,
                    look=LookModel.from_orm(look) if look else None,
                    is_active=attendee.is_active,
                    user=AttendeeUserModel(
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                    ),
                )
            )

        return attendees

    def get_attendees_for_event(self, event_id: uuid.UUID) -> List[AttendeeModel]:
        event = Event.query.filter_by(id=event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        attendees: Dict[uuid.UUID, List[AttendeeModel]]() = self.get_attendees_for_events([event_id])

        if not attendees:
            return []

        return attendees[event_id]

    def create_attendee(self, create_attendee: CreateAttendeeModel) -> AttendeeModel:
        event = Event.query.filter(Event.id == create_attendee.event_id, Event.is_active).first()

        if not event:
            raise NotFoundError("Event not found.")

        attendee_user = None

        try:
            attendee_user = self.user_service.get_user_by_email(create_attendee.email)
        except NotFoundError:
            pass

        if not attendee_user:
            attendee_user = self.user_service.create_user(
                CreateUserModel(
                    first_name=create_attendee.first_name,
                    last_name=create_attendee.last_name,
                    email=create_attendee.email,
                    account_status=False,
                )
            )

        attendee = Attendee.query.filter(
            Attendee.event_id == create_attendee.event_id,
            Attendee.user_id == attendee_user.id,
            Attendee.is_active,
        ).first()

        if attendee:
            raise DuplicateError("Attendee already exists.")
        else:
            try:
                new_attendee = Attendee(
                    id=uuid.uuid4(),
                    user_id=attendee_user.id,
                    event_id=create_attendee.event_id,
                    style=create_attendee.style,
                    invite=create_attendee.invite,
                    pay=create_attendee.pay,
                    size=create_attendee.size,
                    ship=create_attendee.ship,
                    role_id=create_attendee.role_id,
                    look_id=create_attendee.look_id,
                    is_active=create_attendee.is_active,
                )

                db.session.add(new_attendee)
                db.session.commit()
                db.session.refresh(new_attendee)
            except Exception as e:
                raise ServiceError("Failed to create attendee.", e)

            return AttendeeModel.from_orm(new_attendee)

    def update_attendee(self, attendee_id: uuid.UUID, update_attendee: UpdateAttendeeModel) -> AttendeeModel:
        attendee = Attendee.query.filter(Attendee.id == attendee_id, Attendee.is_active).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.style = update_attendee.style
        attendee.invite = update_attendee.invite
        attendee.pay = update_attendee.pay
        attendee.size = update_attendee.size
        attendee.ship = update_attendee.ship
        attendee.role_id = update_attendee.role_id
        attendee.look_id = update_attendee.look_id
        attendee.updated_at = datetime.now()

        try:
            db.session.commit()
            db.session.refresh(attendee)
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

        return AttendeeModel.from_orm(attendee)

    def send_invite(self, attendee_id: uuid.UUID) -> None:
        pass

    def delete_attendee(self, attendee_id: uuid.UUID) -> None:
        attendee = Attendee.query.filter(Attendee.id == attendee_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.is_active = False

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to deactivate attendee.", e)
