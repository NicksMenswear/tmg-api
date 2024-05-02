import uuid

from sqlalchemy import or_

from server.database.database_manager import db
from server.database.models import Event, User, Attendee, Look
from server.services import ServiceError, NotFoundError, DuplicateError


class EventService:
    def get_event_by_id(self, event_id):
        return Event.query.filter_by(id=event_id).first()

    def get_event_by_user_id(self, user_id):
        return Event.query.filter_by(user_id=user_id).first()  # TODO: this is bug!

    def get_events_for_user(self, email, include_attendees=False):
        results = (
            Event.query.join(Attendee, Event.id == Attendee.event_id)
            .join(User, User.id == Attendee.attendee_id)
            .filter(or_(User.email == email, User.id == Event.user_id), Event.is_active)
            .all()
        )

        events = [event.to_dict() for event in results]

        if not include_attendees:
            return events

        for event in events:
            results = (
                db.session.query(Attendee, User, Look)
                .join(User, User.id == Attendee.attendee_id)
                .outerjoin(Look, Look.id == Attendee.look_id)
                .filter(Attendee.event_id == event["id"])
                .all()
            )

            event["attendees"] = []

            for attendee, user, look in results:
                event["attendees"].append(
                    {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "look_id": attendee.look_id,
                        "look_name": look.look_name if look else None,
                        "role": attendee.role,
                    }
                )

        return events

    def get_events_with_attendees_by_user_email(self, email):
        from server.services.look import LookService

        look_service = LookService()

        user = User.query.filter_by(email=email).first()

        if not user:
            raise NotFoundError("User not found.")

        attendees = Attendee.query.filter(Attendee.attendee_id == user.id).all()

        response = []

        for attendee in attendees:
            event = Event.query.filter(Event.id == attendee.event_id, Event.is_active).first()

            if event is None:
                continue

            enriched_attendee = {
                "event_id": event.id,
                "event_name": event.event_name,
                "event_date": str(event.event_date),
                "user_id": str(event.user_id),
            }

            if attendee.look_id:
                look = look_service.get_look_by_id(attendee.look_id)

                if look:
                    enriched_attendee["look_id"] = look.id
                    enriched_attendee["look_name"] = look.look_name

            response.append(enriched_attendee)

        return response

    def create_event(self, event_data):
        user = User.query.filter_by(email=event_data["email"]).first()

        if not user:
            raise NotFoundError("User not found.")

        event = Event.query.filter(
            Event.event_name == event_data["event_name"], Event.is_active, Event.user_id == user.id
        ).first()

        if event:
            raise DuplicateError("Event with the same detail already exists.")

        try:
            event = Event(
                id=event_data.get("id", uuid.uuid4()),
                event_name=event_data.get("event_name"),
                event_date=event_data.get("event_date"),
                user_id=user.id,
                is_active=event_data.get("is_active", True),
            )

            db.session.add(event)
            db.session.commit()
            db.session.refresh(event)
        except Exception as e:
            raise ServiceError("Failed to create event.", e)

        return event

    def update_event(self, event_data):
        event = Event.query.filter(Event.id == event_data["id"], Event.user_id == event_data["user_id"]).first()

        if not event:
            raise NotFoundError("Event not found.")

        try:
            event.event_date = event_data.get("event_date", event.event_date)

            db.session.commit()
            db.session.refresh(event)
        except Exception as e:
            raise ServiceError("Failed to update event.", e)

        return event

    def soft_delete_event(self, event_data):
        event = Event.query.filter(Event.id == event_data["event_id"], Event.user_id == event_data["user_id"]).first()

        if not event:
            raise NotFoundError("Event not found.")

        try:
            event.is_active = event_data.get("is_active", False)  # TODO: this is bug! it should always be false

            db.session.commit()
            db.session.refresh(event)
        except Exception as e:
            raise ServiceError("Failed to delete event.", e)
