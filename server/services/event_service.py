import uuid
from datetime import datetime, timedelta
from typing import List

from server.database.database_manager import db
from server.database.models import Event, User, Attendee, Look, EventType
from server.models.event_model import CreateEventModel, EventModel, UpdateEventModel, EventUserStatus
from server.models.role_model import CreateRoleModel
from server.models.user_model import UserModel
from server.services import ServiceError, NotFoundError, DuplicateError, BadRequestError
from server.services.attendee_service import AttendeeService
from server.services.look_service import LookService
from server.services.role_service import RoleService, PREDEFINED_ROLES

NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION = 4


# noinspection PyMethodMayBeStatic
class EventService:
    def __init__(self, attendee_service: AttendeeService, role_service: RoleService, look_service: LookService):
        self.role_service = role_service
        self.look_service = look_service
        self.attendee_service = attendee_service

    def get_event_by_id(self, event_id: uuid.UUID, enriched=False) -> EventModel:
        event_with_owner = (
            db.session.query(Event, User).join(User, User.id == Event.user_id).filter(Event.id == event_id).first()
        )

        if not event_with_owner:
            raise NotFoundError("Event not found.")

        event_model = EventModel.from_orm(event_with_owner[0])
        event_model.owner = UserModel.from_orm(event_with_owner[1])

        if enriched:
            attendees = self.attendee_service.get_attendees_for_events([event_model.id])
            looks = self.look_service.get_looks_by_user_id(event_model.user_id)
            roles = self.role_service.get_roles_for_events([event_model.id])

            event_model.attendees = attendees.get(event_model.id, [])
            event_model.looks = looks
            event_model.roles = roles.get(event_model.id, [])

        return event_model

    def create_event(
        self, create_event: CreateEventModel, ignore_event_date_creation_condition: bool = False
    ) -> EventModel:
        user = User.query.filter_by(id=create_event.user_id).first()

        if not user:
            raise NotFoundError("User not found.")

        db_event = Event.query.filter(
            Event.name == create_event.name,
            Event.event_at == create_event.event_at,
            Event.is_active,
            Event.user_id == user.id,
        ).first()

        if db_event:
            raise DuplicateError("Event with the same name and date already exists.")

        if not ignore_event_date_creation_condition and not self.__is_ahead_n_weeks(
            create_event.event_at, NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION
        ):
            raise BadRequestError(
                f"You can only create events up to {NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION} weeks in advance. Please choose a date that is within the next {NUMBER_OF_WEEKS_IN_ADVANCE_FOR_EVENT_CREATION} weeks."
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

        event = EventModel.from_orm(db_event)
        event.owner = UserModel.from_orm(user)

        return event

    def update_event(self, event_id: uuid.UUID, update_event: UpdateEventModel) -> EventModel:
        db_event = Event.query.filter(Event.id == event_id, Event.is_active).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        existing_event = Event.query.filter(
            Event.name == update_event.name,
            Event.is_active,
            Event.user_id == db_event.user_id,
            Event.event_at == update_event.event_at,
            Event.id != event_id,
        ).first()

        if existing_event:
            raise DuplicateError("Event with the same details already exists.")

        try:
            db_event.event_at = update_event.event_at
            db_event.name = update_event.name
            db_event.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(db_event)
        except Exception as e:
            raise ServiceError("Failed to update event.", e)

        event = EventModel.from_orm(db_event)
        event.owner = UserModel.from_orm(User.query.filter(User.id == db_event.user_id).first())

        return event

    def delete_event(self, event_id: uuid.UUID, force: bool = False) -> None:
        db_event = Event.query.filter(Event.id == event_id).first()

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
                self.attendee_service.delete_attendee(attendee.id)

            db_event.is_active = False

            db.session.commit()
            db.session.refresh(db_event)
        except Exception as e:
            raise ServiceError("Failed to deactivate event.", e)

    def get_user_owned_events(self, user_id: uuid.UUID, enriched: bool = False) -> List[EventModel]:
        events = (
            db.session.query(Event, User)
            .join(User, User.id == Event.user_id)
            .filter(Event.user_id == user_id, Event.is_active)
            .all()
        )

        if not events:
            return []

        models = []
        for event, user in events:
            event_model = EventModel.from_orm(event)
            event_model.owner = UserModel.from_orm(user)
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

        return models

    def get_user_invited_events(self, user_id: uuid.UUID, enriched: bool = False) -> List[EventModel]:
        events_with_owners = (
            db.session.query(Event, User)
            .join(User, User.id == Event.user_id)
            .join(Attendee, Event.id == Attendee.event_id)
            .filter(Attendee.user_id == user_id, Event.is_active, Attendee.is_active, Attendee.invite)
            .filter(Attendee.user_id != Event.user_id)  # hide own events from invites
            .all()
        )

        events = []

        for event, user in events_with_owners:
            event_model = EventModel.from_orm(event)
            event_model.owner = UserModel.from_orm(user)
            events.append(event_model)

        if not events:
            return []

        if enriched:
            event_ids = [event.id for event in events]
            attendees = self.attendee_service.get_attendees_for_events(event_ids, user_id)

            for event_model in events:
                event_model.attendees = attendees.get(event_model.id, [])

        return events

    def get_user_events(
        self, user_id: uuid.UUID, status: EventUserStatus = None, enriched: bool = False
    ) -> List[EventModel]:
        user = User.query.filter_by(id=user_id).first()

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

    def get_events_for_look(self, look_id: uuid.UUID) -> List[EventModel]:
        db_look = Look.query.filter(Look.id == look_id).first()

        if not db_look:
            raise NotFoundError("Look not found")

        events = (
            Event.query.join(Attendee, Event.id == Attendee.event_id)
            .filter(Attendee.look_id == look_id, Event.is_active)
            .all()
        )

        return [EventModel.from_orm(event) for event in events]

    def __is_ahead_n_weeks(self, event_at: datetime, number_of_weeks: int) -> bool:
        return event_at > datetime.now() + timedelta(weeks=number_of_weeks)
