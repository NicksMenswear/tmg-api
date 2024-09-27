import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy import and_, func

from server.database.database_manager import db
from server.database.models import Attendee, DiscountType, Event, User, Role, Look, Size, Order
from server.flask_app import FlaskApp
from server.models.attendee_model import (
    AttendeeModel,
    CreateAttendeeModel,
    UpdateAttendeeModel,
    EnrichedAttendeeModel,
    AttendeeUserModel,
    TrackingModel,
)
from server.models.event_model import EventModel
from server.models.look_model import LookModel
from server.models.role_model import RoleModel
from server.models.user_model import UserModel, CreateUserModel
from server.services import DuplicateError, ServiceError, NotFoundError, BadRequestError
from server.services.email_service import AbstractEmailService
from server.services.integrations.shopify_service import AbstractShopifyService, logger
from server.services.user_service import UserService

STAGE = os.getenv("STAGE")


class AttendeeService:
    def __init__(
        self, shopify_service: AbstractShopifyService, user_service: UserService, email_service: AbstractEmailService
    ):
        self.shopify_service = shopify_service
        self.user_service = user_service
        self.email_service = email_service

    @staticmethod
    def get_attendee_by_id(attendee_id: uuid.UUID, is_active: bool = True) -> AttendeeModel:
        attendee = Attendee.query.filter(Attendee.id == attendee_id, Attendee.is_active == is_active).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        return AttendeeModel.from_orm(attendee)

    @staticmethod
    def get_num_attendees_for_event(event_id: uuid.UUID) -> int:
        db_event = Event.query.filter_by(id=event_id, is_active=True).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        return Attendee.query.filter_by(event_id=db_event.id, is_active=True).count()

    @staticmethod
    def get_num_discountable_attendees_for_event(event_id: uuid.UUID) -> int:
        return Attendee.query.filter(
            Attendee.event_id == event_id,
            Attendee.is_active == True,
            # Attendee.look_id != None,
            # Attendee.style == True,
            # Attendee.invite == True,
        ).count()

    def get_attendees_for_events(
        self, event_ids: List[uuid.UUID], user_id: Optional[uuid.UUID] = None
    ) -> Dict[uuid.UUID, List[EnrichedAttendeeModel]]:

        query = (
            db.session.query(
                Attendee,
                Event,
                User,
                Role,
                Look,
                func.array_agg(
                    func.json_build_object(
                        "outbound_tracking", Order.outbound_tracking, "shopify_order_id", Order.shopify_order_id
                    )
                ).label("order_tracking"),
            )
            .join(Event, Event.id == Attendee.event_id)
            .outerjoin(User, User.id == Attendee.user_id)
            .outerjoin(Role, Attendee.role_id == Role.id)
            .outerjoin(Look, Attendee.look_id == Look.id)
            .outerjoin(Order, and_(Order.event_id == Attendee.event_id, Order.user_id == Attendee.user_id))
            .filter(Attendee.event_id.in_(event_ids), Attendee.is_active)
            .group_by(Attendee.id, Event.id, User.id, Role.id, Look.id)
            .order_by(Attendee.created_at.asc())
        )

        if user_id is not None:
            query = query.filter(Attendee.user_id == user_id)

        db_attendees = query.all()

        if not db_attendees:
            return {}

        attendees = {}

        attendee_ids = {attendee.id for attendee, _, _, _, _, _ in db_attendees}
        attendees_gift_codes = FlaskApp.current().discount_service.get_discount_codes_for_attendees(
            attendee_ids, type=DiscountType.GIFT
        )

        for attendee, event, user, role, look, orders in db_attendees:
            if attendee.event_id not in attendees:
                attendees[attendee.event_id] = list()

            attendee_gift_codes = attendees_gift_codes.get(attendee.id, set())
            has_gift_codes = len(attendee_gift_codes) > 0
            attendee_tracking = self.__get_tracking_for_attendee(orders)

            attendees[attendee.event_id].append(
                EnrichedAttendeeModel(
                    id=attendee.id,
                    first_name=attendee.first_name or user.first_name,
                    last_name=attendee.last_name or user.last_name,
                    email=attendee.email or user.email if user else None,
                    user_id=attendee.user_id,
                    is_owner=(attendee.user_id == event.user_id),
                    event_id=attendee.event_id,
                    style=attendee.style,
                    invite=attendee.invite,
                    pay=attendee.pay,
                    size=attendee.size,
                    ship=attendee.ship or bool(attendee_tracking),
                    role_id=attendee.role_id,
                    look_id=attendee.look_id,
                    role=RoleModel.from_orm(role) if role else None,
                    look=LookModel.from_orm(look) if look else None,
                    is_active=attendee.is_active,
                    gift_codes=attendee_gift_codes,
                    has_gift_codes=has_gift_codes,
                    tracking=attendee_tracking,
                    can_be_deleted=(attendee.pay is False and len(attendee_gift_codes) == 0),
                    user=AttendeeUserModel(
                        first_name=user.first_name if user else attendee.first_name,
                        last_name=user.last_name if user else attendee.last_name,
                        email=user.email if user else attendee.email,
                    ),
                )
            )

        # Show owner of event on top of the attendee list
        for event_id, event_attendees in attendees.items():
            attendees[event_id] = sorted(event_attendees, key=lambda a: a.is_owner, reverse=True)

        return attendees

    @staticmethod
    def update_attendee_pay_status(event_id: uuid.UUID, user_id: uuid.UUID):
        attendee = Attendee.query.filter(
            Attendee.event_id == event_id, Attendee.user_id == user_id, Attendee.is_active
        ).first()

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

        if create_attendee.email:
            try:
                attendee_user = self.user_service.get_user_by_email(create_attendee.email)
            except NotFoundError:
                pass

        if attendee_user:
            attendee = Attendee.query.filter(
                Attendee.event_id == create_attendee.event_id,
                Attendee.user_id == attendee_user.id,
                Attendee.is_active,
            ).first()

            if attendee:
                raise DuplicateError("Attendee already exists.")

        try:
            user_size = Size.query.filter(Size.user_id == attendee_user.id).first() if attendee_user else None
            owner_auto_invite = event.user_id == attendee_user.id if attendee_user else False
            new_attendee = Attendee(
                id=uuid.uuid4(),
                first_name=create_attendee.first_name,
                last_name=create_attendee.last_name,
                email=create_attendee.email,
                user_id=attendee_user.id if attendee_user else None,
                event_id=create_attendee.event_id,
                role_id=create_attendee.role_id,
                look_id=create_attendee.look_id,
                is_active=create_attendee.is_active,
                size=bool(user_size),
                style=create_attendee.style,
                invite=create_attendee.invite or owner_auto_invite,
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

        self.__update_look(attendee, update_attendee)
        self.__update_email(attendee, update_attendee)

        attendee.first_name = update_attendee.first_name or attendee.first_name
        attendee.last_name = update_attendee.last_name or attendee.last_name
        attendee.role_id = update_attendee.role_id or attendee.role_id
        attendee.style = True if attendee.role_id and attendee.look_id else False
        attendee.updated_at = datetime.now()

        try:
            db.session.commit()
            db.session.refresh(attendee)
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

        return AttendeeModel.from_orm(attendee)

    @staticmethod
    def __is_attendee_paid_or_has_discount(attendee: Attendee) -> bool:
        return attendee.pay or FlaskApp.current().discount_service.get_discount_codes_for_attendees(
            [attendee.id], type=DiscountType.GIFT
        ).get(attendee.id)

    def __update_look(self, attendee: Attendee, update_attendee: UpdateAttendeeModel) -> None:
        if update_attendee.look_id is None:
            # pass, no new look - nothing to do
            return

        if attendee.look_id is None:
            # pass, no look set before - setting now
            attendee.look_id = update_attendee.look_id
            return

        if attendee.look_id == update_attendee.look_id:
            # pass, same look - nothing to do
            return

        if self.__is_attendee_paid_or_has_discount(attendee):
            raise BadRequestError("Cannot update look for attendee that has already paid or has an issued gift code.")

        attendee.look_id = update_attendee.look_id

    def __update_email(self, attendee: Attendee, update_attendee: UpdateAttendeeModel) -> None:
        if update_attendee.email is None:
            # pass, no email - nothing to do
            return

        if attendee.email is None:
            # email wasn't set before, setting now
            attendee.email = update_attendee.email
            return

        if attendee.email == update_attendee.email:
            # pass, same email - nothing to do
            return

        if attendee.user_id is None:
            # pass, user not invited yet - just updating email
            attendee.email = update_attendee.email
            return

        if self.__is_attendee_paid_or_has_discount(attendee):
            raise BadRequestError("Cannot update email for attendee that has already paid or has an issued gift code.")
        else:
            attendee.user_id = None
            attendee.email = update_attendee.email
            attendee.invite = False
            attendee.size = False

    @staticmethod
    def deactivate_attendee(attendee_id: uuid.UUID, force: bool = False) -> None:
        attendee = Attendee.query.filter(Attendee.id == attendee_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        if not force and attendee.is_active and attendee.pay:
            raise BadRequestError("Cannot delete attendee that has paid.")

        attendee.is_active = False

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to deactivate attendee.", e)

    def send_invites(self, attendee_ids: List[uuid.UUID]) -> None:
        if not attendee_ids:
            return

        rows = (
            db.session.query(Attendee, Event)
            .join(Event, Event.id == Attendee.event_id)
            .filter(Attendee.id.in_(attendee_ids), Attendee.is_active)
            .all()
        )

        if not rows:
            return

        attendees = [attendee for attendee, _ in rows]

        invited_users: list[UserModel] = []
        invited_attendees: list[Attendee] = []

        for attendee in attendees:
            if attendee.user_id is not None:
                # user already associated with attendee
                invited_users.append(self.user_service.get_user_by_id(attendee.user_id))
                invited_attendees.append(attendee)

                continue

            if attendee.email is None:
                logger.error(f"Attendee {attendee.id} has no email.")
                continue

            try:
                user = self.user_service.get_user_by_email(attendee.email)
                attendee.user_id = user.id

                db.session.commit()

                invited_attendees.append(attendee)
                invited_users.append(user)
            except NotFoundError:
                try:
                    user = self.user_service.create_user(
                        CreateUserModel(
                            first_name=attendee.first_name, last_name=attendee.last_name, email=attendee.email
                        )
                    )
                    attendee.user_id = user.id

                    db.session.commit()

                    invited_users.append(user)
                    invited_attendees.append(attendee)
                except Exception:
                    logger.exception(f"Failed to create user for attendee {attendee.id}.")

        if not invited_users:
            return

        event = EventModel.from_orm(rows[0][1])

        self.email_service.send_invites_batch(event, invited_users)

        try:
            for attendee in attendees:
                attendee.invite = True

            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

    @staticmethod
    def __get_tracking_for_attendee(orders) -> List[TrackingModel]:
        shop_id = FlaskApp.current().online_store_shop_id
        tracking = []

        for order in orders:
            if not order:
                continue
            if order.get("outbound_tracking"):
                tracking_number = order.get("outbound_tracking")
                if STAGE == "prd":
                    tracking_url = f"https://account.themoderngroom.com/orders/{order.get('shopify_order_id')}"
                else:
                    tracking_url = f"https://shopify.com/{shop_id}/account/orders/{order.get('shopify_order_id')}"
                tracking.append(TrackingModel(tracking_number=tracking_number, tracking_url=tracking_url))

        return tracking

    @staticmethod
    def find_attendees_by_look_id(look_id: uuid.UUID) -> List[AttendeeModel]:
        attendees = Attendee.query.filter(Attendee.look_id == look_id, Attendee.is_active).all()

        return [AttendeeModel.from_orm(attendee) for attendee in attendees]
