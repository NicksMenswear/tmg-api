import uuid
from datetime import datetime
from typing import List, Dict, Optional

from server.database.database_manager import db
from server.database.models import Attendee, Event, User, Role, Look, Size, Order
from server.flask_app import FlaskApp
from server.models.attendee_model import (
    AttendeeModel,
    CreateAttendeeModel,
    UpdateAttendeeModel,
    EnrichedAttendeeModel,
    AttendeeUserModel,
    TrackingModel,
)
from server.models.look_model import LookModel
from server.models.role_model import RoleModel
from server.models.user_model import CreateUserModel, UserModel
from server.models.event_model import EventModel
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.email import AbstractEmailService
from server.services.shopify import AbstractShopifyService
from server.services.user import UserService


# noinspection PyMethodMayBeStatic
class AttendeeService:
    def __init__(
        self, shopify_service: AbstractShopifyService, user_service: UserService, email_service: AbstractEmailService
    ):
        self.shopify_service = shopify_service
        self.user_service = user_service
        self.email_service = email_service

    def get_attendee_by_id(self, attendee_id: uuid.UUID, is_active: bool = True) -> AttendeeModel:
        attendee = Attendee.query.filter(Attendee.id == attendee_id, Attendee.is_active == is_active).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        return AttendeeModel.from_orm(attendee)

    def get_num_attendees_for_event(self, event_id: uuid.UUID) -> int:
        db_event = Event.query.filter_by(id=event_id, is_active=True).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        return Attendee.query.filter_by(event_id=db_event.id, is_active=True).count()

    def get_num_discountable_attendees_for_event(self, event_id: uuid.UUID) -> int:
        return Attendee.query.filter(
            Attendee.event_id == event_id,
            Attendee.is_active == True,
            Attendee.look_id != None,
            Attendee.style == True,
            Attendee.invite == True,
        ).count()

    def get_attendees_for_events(
        self, event_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> Dict[uuid.UUID, List[EnrichedAttendeeModel]]:
        query = (
            db.session.query(Attendee, User, Role, Look)
            .join(Event, Event.id == Attendee.event_id)
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
            return {}

        attendees = {}

        attendee_ids = {attendee.id for attendee, _, _, _, _ in db_attendees}

        attendees_gift_codes = FlaskApp.current().discount_service.get_discount_codes_for_attendees(attendee_ids)

        for attendee, event, user, role, look in db_attendees:
            if attendee.event_id not in attendees:
                attendees[attendee.event_id] = list()

            attendees[attendee.event_id].append(
                EnrichedAttendeeModel(
                    id=attendee.id,
                    user_id=attendee.user_id,
                    is_owner=(attendee.user_id == event.user_id),
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
                    gift_codes=attendees_gift_codes.get(attendee.id, set()),
                    tracking=self._get_tracking_for_attendee(attendee),
                    user=AttendeeUserModel(
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                    ),
                )
            )

        # Show owner of event on top of the attendee list
        for event_id, event_attendees in attendees.items():
            attendees[event_id] = sorted(event_attendees, key=lambda a: a.is_owner, reverse=True)

        return attendees

    def update_attendee_pay_status(self, event_id: uuid.UUID, user_id: uuid.UUID):
        attendee = Attendee.query.filter(Attendee.event_id == event_id, Attendee.user_id == user_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.pay = True

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to update attendee pay status.", e)

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
                user_size = Size.query.filter(Size.user_id == attendee_user.id).first()
                new_attendee = Attendee(
                    id=uuid.uuid4(),
                    user_id=attendee_user.id,
                    event_id=create_attendee.event_id,
                    role_id=create_attendee.role_id,
                    look_id=create_attendee.look_id,
                    is_active=create_attendee.is_active,
                    size=bool(user_size),
                    style=create_attendee.style,
                    invite=create_attendee.invite,
                    pay=create_attendee.pay,
                    ship=create_attendee.ship,
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

        attendee.role_id = update_attendee.role_id or attendee.role_id
        attendee.look_id = update_attendee.look_id or attendee.look_id
        attendee.style = True if attendee.role_id and attendee.look_id else False
        attendee.updated_at = datetime.now()

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

    def send_invites(self, attendee_ids: List[uuid.UUID]) -> None:
        if not attendee_ids:
            return
        rows = (
            db.session.query(User, Attendee, Event)
            .join(Attendee, Attendee.user_id == User.id)
            .join(Event, Event.id == Attendee.event_id)
            .filter(Attendee.id.in_(attendee_ids))
            .all()
        )
        user_models = [UserModel.from_orm(user) for user, attendee, event in rows]
        event_model = EventModel.from_orm(rows[0][2])

        self.email_service.send_invites_batch(event_model, user_models)

        for user, attendee, event in rows:
            attendee.invite = True

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

    def _get_tracking_for_attendee(self, attendee: Attendee) -> List[TrackingModel]:
        shop_id = FlaskApp.current().online_store_shop_id
        tracking = []
        orders = Order.query.filter(Order.event_id == attendee.event_id, Order.user_id == attendee.user_id).all()
        for order in orders:
            if order.outbound_tracking:
                tracking_number = order.outbound_tracking
                tracking_url = f"https://shopify.com/{shop_id}/account/orders/{order.shopify_order_id}"
                tracking.append(TrackingModel(tracking_number=tracking_number, tracking_url=tracking_url))
        return tracking
