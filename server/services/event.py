import uuid
from datetime import datetime
from typing import List

from server.database.database_manager import db
from server.database.models import Event, User, Attendee, Look
from server.models.event_model import CreateEventModel, EventModel, UpdateEventModel, EventUserStatus
from server.services import ServiceError, NotFoundError, DuplicateError


# noinspection PyMethodMayBeStatic
class EventService:
    def get_event_by_id(self, event_id: uuid.UUID) -> EventModel:
        event = Event.query.filter_by(id=event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        return EventModel.from_orm(event)

    # def get_enriched_event_by_id(self, event_id):
    #     event = Event.query.filter_by(id=event_id).first()
    #
    #     if not event:
    #         raise NotFoundError("Event not found.")
    #
    #     event = event.to_dict()
    #
    #     event["attendees"] = []
    #
    #     results = (
    #         db.session.query(Attendee, User, Look, Role)
    #         .join(Event, Event.id == Attendee.event_id)
    #         .join(User, User.id == Attendee.user_id)
    #         .outerjoin(Look, Look.id == Attendee.look_id)
    #         .outerjoin(Role, Role.id == Attendee.role)
    #         .filter(Event.id == event_id, Attendee.is_active)
    #         .all()
    #     )
    #
    #     for attendee, user, look, role in results:
    #         attendee = {
    #             "id": attendee.id,
    #             "invite": attendee.invite,
    #             "pay": attendee.pay,
    #             "ship": attendee.ship,
    #             "size": attendee.size,
    #             "style": attendee.style,
    #             "user": {
    #                 "id": user.id,
    #                 "first_name": user.first_name,
    #                 "last_name": user.last_name,
    #                 "email": user.email,
    #             },
    #             "look": None,
    #             "role": None,
    #         }
    #
    #         if look:
    #             attendee["look"] = {
    #                 "id": look.id,
    #                 "name": look.name,
    #                 "product_specs": look.product_specs,
    #             }
    #
    #         if role:
    #             attendee["role"] = {
    #                 "id": role.id,
    #                 "name": role.name,
    #             }
    #
    #         event["attendees"].append(attendee)
    #
    #     return event

    def get_num_attendees_for_event(self, event_id: uuid.UUID) -> int:
        db_event = Event.query.filter_by(id=event_id, is_active=True).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        return Attendee.query.filter_by(event_id=db_event.id, is_active=True).count()

    def create_event(self, create_event: CreateEventModel) -> EventModel:
        user = User.query.filter_by(id=create_event.user_id).first()

        if not user:
            raise NotFoundError("User not found.")

        db_event = Event.query.filter(
            Event.name == create_event.name, Event.is_active, Event.user_id == user.id
        ).first()

        if db_event:
            raise DuplicateError("Event with the same details already exists.")

        try:
            db_event = Event(
                name=create_event.name,
                event_at=create_event.event_at,
                user_id=user.id,
                is_active=create_event.is_active,
            )

            db.session.add(db_event)
            db.session.commit()
            db.session.refresh(db_event)
        except Exception as e:
            raise ServiceError("Failed to create event.", e)

        return EventModel.from_orm(db_event)

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

        return EventModel.from_orm(db_event)

    def delete_event(self, event_id: uuid.UUID) -> None:
        db_event = Event.query.filter(Event.id == event_id).first()

        if not db_event:
            raise NotFoundError("Event not found.")

        try:
            db_event.is_active = False

            db.session.commit()
            db.session.refresh(db_event)
        except Exception as e:
            raise ServiceError("Failed to deactivate event.", e)

    def get_user_owned_events(self, user_id: uuid.UUID) -> List[EventModel]:
        return [EventModel.from_orm(event) for event in Event.query.filter_by(user_id=user_id, is_active=True).all()]

    def get_user_invited_events(self, user_id: uuid.UUID) -> List[EventModel]:
        return [
            EventModel.from_orm(event)
            for event in (
                Event.query.join(Attendee, Event.id == Attendee.event_id)
                .filter(Attendee.user_id == user_id, Event.is_active)
                .all()
            )
        ]

    def get_user_events(self, user_id: uuid.UUID, status: EventUserStatus = None) -> List[EventModel]:
        user = User.query.filter_by(id=user_id).first()

        if not user:
            raise NotFoundError("User not found.")

        owned_events = []
        invited_events = []

        if not status or status == EventUserStatus.OWNER:
            owned_events = self.get_user_owned_events(user_id)

        if not status or status == EventUserStatus.ATTENDEE:
            invited_events = self.get_user_invited_events(user_id)

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
