import uuid
from typing import List

from server.database.database_manager import db
from server.database.models import Attendee, Event
from server.models.attendee_model import AttendeeModel, CreateAttendeeModel, UpdateAttendeeModel
from server.models.user_model import CreateUserModel
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.event import EventService
from server.services.shopify import AbstractShopifyService
from server.services.user import UserService


# noinspection PyMethodMayBeStatic
class AttendeeService:
    def __init__(
        self,
        shopify_service: AbstractShopifyService,
        user_service: UserService,
        event_service: EventService,
    ):
        self.shopify_service = shopify_service
        self.user_service = user_service
        self.event_service = event_service

    def get_attendee_by_id(self, attendee_id: uuid.UUID, is_active: bool = True) -> AttendeeModel:
        attendee = Attendee.query.filter(Attendee.id == attendee_id, Attendee.is_active == is_active).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        return AttendeeModel.from_orm(attendee)

    def get_attendees_for_event(self, event_id: uuid.UUID) -> List[AttendeeModel]:
        event = Event.query.filter_by(id=event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        attendees = Attendee.query.filter(Attendee.event_id == event_id, Attendee.is_active).all()

        return [AttendeeModel.from_orm(attendee) for attendee in attendees]

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
            Attendee.attendee_id == attendee_user.id,
            Attendee.is_active,
        ).first()

        if attendee:
            raise DuplicateError("Attendee already exists.")
        else:
            try:
                new_attendee = Attendee(
                    id=uuid.uuid4(),
                    attendee_id=attendee_user.id,
                    event_id=create_attendee.event_id,
                    style=create_attendee.style,
                    invite=create_attendee.invite,
                    pay=create_attendee.pay,
                    size=create_attendee.size,
                    ship=create_attendee.ship,
                    role=create_attendee.role,
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
        attendee.role = update_attendee.role
        attendee.look_id = update_attendee.look_id

        try:
            db.session.commit()
            db.session.refresh(attendee)
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

        return AttendeeModel.from_orm(attendee)

    def delete_attendee(self, attendee_id: uuid.UUID) -> None:
        attendee = Attendee.query.filter(Attendee.id == attendee_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.is_active = False

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to deactivate attendee.", e)
