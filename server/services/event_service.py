import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, func

from server.database.database_manager import db
from server.database.models import Event, User, Attendee, Look, EventType
from server.models.event_model import CreateEventModel, EventModel, UpdateEventModel, EventUserStatus, AttendeeModel
from server.models.role_model import CreateRoleModel
from server.models.user_model import UserModel
from server.services import ServiceError, NotFoundError, DuplicateError, BadRequestError
from server.services.attendee_service import AttendeeService
from server.services.look_service import LookService
from server.services.role_service import RoleService, PREDEFINED_ROLES

NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION = 4


class EventService:
    def __init__(
        self,
        attendee_service: Optional[AttendeeService] = None,
        role_service: Optional[RoleService] = None,
        look_service: Optional[LookService] = None,
    ):
        self.role_service = role_service
        self.look_service = look_service
        self.attendee_service = attendee_service

    def get_event_by_id(self, event_id: uuid.UUID, enriched=False) -> EventModel:
        event_with_owner = db.session.execute(select(Event, User).join(User).where(Event.id == event_id)).first()

        if not event_with_owner:
            raise NotFoundError("Event not found.")

        event_model = EventModel.model_validate(event_with_owner[0])
        event_model.owner = UserModel.model_validate(event_with_owner[1])

        if enriched:
            attendees = self.attendee_service.get_attendees_for_events([event_model.id])
            looks = self.look_service.get_looks_by_user_id(event_model.user_id)
            roles = self.role_service.get_roles_for_events([event_model.id])

            event_model.attendees = attendees.get(event_model.id, [])
            event_model.looks = looks
            event_model.roles = roles.get(event_model.id, [])

        return event_model

    @staticmethod
    def get_events(event_ids: List[uuid.UUID]) -> List[EventModel]:
        events = db.session.execute(select(Event).where(Event.id.in_(event_ids), Event.is_active)).scalars().all()
        return [EventModel.model_validate(event) for event in events]

    def create_event(self, create_event: CreateEventModel) -> EventModel:
        user = db.session.execute(select(User).where(User.id == create_event.user_id)).scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found.")

        db_event = (
            db.session.execute(
                select(Event).where(
                    Event.name == create_event.name,
                    Event.event_at == create_event.event_at,
                    Event.is_active,
                    Event.user_id == user.id,
                )
            )
            .scalars()
            .first()
        )

        if db_event:
            raise DuplicateError("Event with the same name and date already exists.")

        if create_event.event_at and not self.__is_ahead_n_weeks(
            create_event.event_at, NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION
        ):
            raise BadRequestError(
                f"You cannot schedule events within the next {NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION} weeks. Please select a later date."
            )

        try:
            db_event = Event(
                name=create_event.name,
                event_at=create_event.event_at,
                user_id=user.id,
                is_active=create_event.is_active,
                type=EventType(str(create_event.type)),
            )
            db.session.add(db_event)
            db.session.flush()

            roles = [
                CreateRoleModel(name=role, event_id=db_event.id) for role in PREDEFINED_ROLES.get(create_event.type, [])
            ]
            self.role_service.create_roles(roles)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to create event.", e)

        event = EventModel.model_validate(db_event)
        event.owner = UserModel.model_validate(user)

        return event

    def update_event(self, event_id: uuid.UUID, update_event: UpdateEventModel) -> EventModel:
        db_event = db.session.execute(select(Event).where(Event.id == event_id, Event.is_active)).scalar_one_or_none()

        if not db_event:
            raise NotFoundError("Event not found.")

        existing_event = (
            db.session.execute(
                select(Event).where(
                    Event.name == update_event.name,
                    Event.is_active,
                    Event.user_id == db_event.user_id,
                    Event.event_at == update_event.event_at,
                    Event.id != event_id,
                )
            )
            .scalars()
            .first()
        )

        if existing_event:
            raise DuplicateError("Event with the same details already exists.")

        if update_event.event_at and not self.__is_ahead_n_weeks(
            update_event.event_at, NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION
        ):
            raise BadRequestError(
                f"You cannot edit events scheduled within the next {NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION} weeks. Please choose a later date."
            )

        try:
            db_event.event_at = update_event.event_at
            db_event.name = update_event.name
            db_event.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(db_event)
        except Exception as e:
            raise ServiceError("Failed to update event.", e)

        event = EventModel.model_validate(db_event)
        event.owner = UserModel.model_validate(
            db.session.execute(select(User).where(User.id == db_event.user_id)).scalar_one_or_none()
        )

        return event

    def delete_event(self, event_id: uuid.UUID, force: bool = False) -> None:
        db_event = db.session.execute(select(Event).where(Event.id == event_id)).scalar_one_or_none()

        if not db_event:
            raise NotFoundError("Event not found.")

        attendees = self.attendee_service.get_attendees_for_event(db_event.id)

        has_invited_or_paid_attendees = any(
            (attendee.is_active and (attendee.invite or attendee.pay)) for attendee in attendees
        )

        if not force and has_invited_or_paid_attendees:
            raise BadRequestError("Cannot delete event with invited or paid attendees.")

        try:
            for attendee in attendees:
                self.attendee_service.deactivate_attendee(attendee.id, force)

            db_event.is_active = False

            db.session.commit()
            db.session.refresh(db_event)
        except Exception as e:
            raise ServiceError("Failed to deactivate event.", e)

    def get_user_owned_events(self, user_id: uuid.UUID, enriched: bool = False) -> List[EventModel]:
        events = db.session.execute(
            select(Event, User).join(User, User.id == Event.user_id).where(Event.user_id == user_id, Event.is_active)
        ).all()

        if not events:
            return []

        models = []
        for event, user in events:
            event_model = EventModel.model_validate(event)
            event_model.owner = UserModel.model_validate(user)
            models.append(event_model)

        if enriched:
            event_ids = [event.id for event in models]
            attendees = self.attendee_service.get_attendees_for_events(event_ids)
            looks = self.look_service.get_looks_by_user_id(user_id)
            roles = self.role_service.get_roles_for_events(event_ids)

            for event_model in models:
                event_model.attendees = attendees.get(event_model.id, [])
                event_model.looks = looks
                event_model.roles = roles.get(event_model.id, [])
                event_model.notifications = self.__owner_notifications(event_model, attendees.get(event_model.id, []))

        return models

    def get_user_invited_events(self, user_id: uuid.UUID, enriched: bool = False) -> List[EventModel]:
        events_with_owners = db.session.execute(
            select(Event, User)
            .join(User, User.id == Event.user_id)
            .join(Attendee, Event.id == Attendee.event_id)
            .where(
                Attendee.user_id == user_id,
                Event.is_active,
                Attendee.is_active,
                Attendee.invite,
                Attendee.user_id != Event.user_id,
            )
        ).all()

        events = []

        for event, user in events_with_owners:
            event_model = EventModel.model_validate(event)
            event_model.owner = UserModel.model_validate(user)
            events.append(event_model)

        if not events:
            return []

        if enriched:
            event_ids = [event.id for event in events]
            attendees = self.attendee_service.get_attendees_for_events(event_ids, user_id)

            for event_model in events:
                event_model.attendees = attendees.get(event_model.id, [])
                event_model.notifications = self.__attendee_notifications(
                    event_model, attendees.get(event_model.id, [])
                )

        return events

    def get_user_events(
        self, user_id: uuid.UUID, status: EventUserStatus = None, enriched: bool = False
    ) -> List[EventModel]:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found.")

        owned_events = []
        invited_events = []

        if not status or status == EventUserStatus.OWNER:
            try:
                owned_events = self.get_user_owned_events(user_id, enriched)
            except Exception as e:
                raise ServiceError("Failed to get user owned events.", e)

        if not status or status == EventUserStatus.ATTENDEE:
            invited_events = self.get_user_invited_events(user_id, enriched)

        combined_events = owned_events + invited_events

        events = {}

        for event in combined_events:
            events[event.id] = event
            events[event.id].status = EventUserStatus.OWNER if event.user_id == user_id else EventUserStatus.ATTENDEE

        return sorted(list(events.values()), key=lambda x: x.event_at)

    @staticmethod
    def get_events_for_look(look_id: uuid.UUID) -> List[EventModel]:
        db_look = db.session.execute(select(Look).where(Look.id == look_id)).scalar_one_or_none()

        if not db_look:
            raise NotFoundError("Look not found")

        events = (
            db.session.execute(
                select(Event)
                .join(Attendee, Event.id == Attendee.event_id)
                .where(Attendee.look_id == look_id, Event.is_active)
            )
            .scalars()
            .all()
        )

        return [EventModel.model_validate(event) for event in events]

    @staticmethod
    def __is_ahead_n_weeks(event_at: datetime, number_of_weeks: int) -> bool:
        if not event_at:
            return True
        return event_at > datetime.now() + timedelta(weeks=number_of_weeks)

    @staticmethod
    def __owner_notifications(event: EventModel, attendees: List[AttendeeModel]) -> List[dict]:
        if not event.event_at:
            return []

        if not any([a.invite for a in attendees]):
            return []

        incomplete_orders = len([a for a in attendees if a.invite and not a.pay])
        if not incomplete_orders:
            return []

        weeks_to_event = (event.event_at - datetime.now()).days // 7
        weeks_to_order = weeks_to_event - 8
        notifications = []
        tooltip = "Grooms receive their suit first, shipping within 1-3 business days after order is placed. This allows you to review fit and quality before extending invitations to your party members. All event party members will receive their shipments 5-6 weeks prior to the event."

        if weeks_to_event <= 12:
            notifications = [
                {
                    "message": f"{weeks_to_order} weeks until all orders in your event need to be completed! Incomplete orders: {incomplete_orders}",
                    "tooltip": tooltip,
                }
            ]
        if weeks_to_event <= 8:
            notifications = [
                {
                    "message": f"{incomplete_orders} orders are due NOW to avoid complications with your event!",
                    "tooltip": tooltip,
                }
            ]
        if weeks_to_event <= 3:
            notifications = [
                {
                    "message": "Your deadline has elapsed, please contact support.",
                    "tooltip": tooltip,
                }
            ]

        if weeks_to_event <= 6:
            notifications.append(
                {
                    "message": "You have less than 6 weeks left to the event. We can still get your order to you, on time, with expedited shipping.",
                    "tooltip": None,
                }
            )

        return notifications

    @staticmethod
    def __attendee_notifications(event: EventModel, attendees: List[AttendeeModel]):
        if not event.event_at:
            return []

        if not attendees:
            return []

        my_attendee = attendees[0]
        if my_attendee.pay:
            return []

        weeks_to_event = (event.event_at - datetime.now()).days // 7
        weeks_to_order = weeks_to_event - 8
        tooltip = None
        notifications = []

        if weeks_to_event <= 12:
            notifications = [
                {
                    "message": f"{weeks_to_order} weeks until your order should be completed!",
                    "tooltip": tooltip,
                }
            ]
        if weeks_to_event <= 8:
            notifications = [
                {
                    "message": "Your order is due NOW.",
                    "tooltip": tooltip,
                }
            ]
        if weeks_to_event <= 3:
            notifications = [
                {
                    "message": "Your deadline has elapsed, please contact support.",
                    "tooltip": tooltip,
                }
            ]

        if weeks_to_event <= 6:
            notifications.append(
                {
                    "message": "You have less than 6 weeks left to the event. We can still get your order to you, on time, with expedited shipping.",
                    "tooltip": None,
                }
            )

        return notifications

    @staticmethod
    def get_user_owned_events_with_n_attendees(user_id: uuid.UUID, n: int) -> List[EventModel]:
        events = (
            db.session.execute(
                select(Event)
                .join(Attendee, Attendee.event_id == Event.id)
                .where(
                    Event.is_active,
                    Attendee.is_active,
                    Attendee.invite,
                    Event.user_id == user_id,
                    Event.event_at > datetime.now(timezone.utc),
                )
                .group_by(Event.id)
                .having(func.count(Attendee.id) >= n)
            )
            .scalars()
            .all()
        )

        if not events:
            return []

        return [EventModel.model_validate(event) for event in events]

    @staticmethod
    def get_user_member_events_with_n_attendees(user_id: uuid.UUID, n: int) -> List[EventModel]:
        user_event_ids = (
            db.session.execute(
                select(Event.id)
                .join(Attendee, Attendee.event_id == Event.id)
                .where(Attendee.user_id == user_id, Attendee.is_active, Event.is_active, Attendee.invite)
            )
            .scalars()
            .all()
        )

        events = (
            db.session.execute(
                select(Event)
                .join(Attendee, Attendee.event_id == Event.id)
                .filter(
                    Attendee.is_active,
                    Event.is_active,
                    Attendee.invite,
                    Event.event_at > datetime.now(timezone.utc),
                    Event.id.in_(user_event_ids),
                )
                .group_by(Event.id)
                .having(func.count(Attendee.id) >= n)
            )
            .scalars()
            .all()
        )

        if not events:
            return []

        return [EventModel.model_validate(event) for event in events]
