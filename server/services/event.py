import uuid

from server.database.models import Event, User, Look, Attendee, Role
from server.services import ServiceError, NotFoundError, DuplicateError
from server.services.base import BaseService
from server.services.look import LookService


class EventService(BaseService):
    def __init__(self, session_factory, shopify_service=None, email_service=None):
        super().__init__(session_factory)

        self.look_service = LookService(session_factory)

    def get_event_by_id(self, event_id):
        with self.session_factory() as db:
            return db.query(Event).filter_by(id=event_id).first()

    def get_event_by_user_id(self, user_id):
        with self.session_factory() as db:
            return db.query(Event).filter_by(user_id=user_id).first()  # TODO: this is bug!

    def get_events_with_looks_by_user_email(self, email):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=email).first()

            if not user:
                raise NotFoundError("User not found.")

            events = db.query(Event).filter(Event.user_id == user.id, Event.is_active).all()

            enriched_events = []

            for event in events:
                enriched_event = {
                    "id": event.id,
                    "event_name": event.event_name,
                    "event_date": str(event.event_date),
                    "user_id": str(event.user_id),
                    "is_active": event.is_active,
                    "looks": [],
                }

                looks = self.look_service.get_looks_by_event_id(event.id)

                for look in looks:
                    enriched_event["looks"].append(
                        {
                            "id": look.id,
                            "look_name": look.look_name,
                            "user_id": look.user_id,
                            "product_specs": look.product_specs,
                            "product_final_image": look.product_final_image,
                        }
                    )

                enriched_events.append(enriched_event)

            return enriched_events

    def get_events_with_attendees_by_user_email(self, email):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=email).first()

            if not user:
                raise NotFoundError("User not found.")

            attendees = db.query(Attendee).filter(Attendee.attendee_id == user.id).all()

            formatted_data = []

            for attendee in attendees:
                event = db.query(Event).filter(Event.id == attendee.event_id, Event.is_active).first()

                if event is None:
                    continue

                role = db.query(Role).filter(Role.id == attendee.role).first()

                if role:
                    look = db.query(Look).filter(Look.id == role.look_id).first()

                    if look is None:
                        look_data = {}
                    else:
                        look_data = {
                            "id": look.id,
                            "look_name": look.look_name,
                            "product_specs": look.product_specs,
                            "product_final_image": look.product_final_image,
                        }
                    data = {
                        "event_id": event.id,
                        "event_name": event.event_name,
                        "event_date": str(event.event_date),
                        "user_id": str(event.user_id),
                        "look_data": look_data,
                    }

                    formatted_data.append(data)
                else:
                    look_data = {}

                    data = {
                        "event_id": event.id,
                        "event_name": event.event_name,
                        "event_date": str(event.event_date),
                        "user_id": str(event.user_id),
                        "look_data": look_data,
                    }

                    formatted_data.append(data)

            return formatted_data

    def create_event(self, **event_data):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=event_data["email"]).first()

            if not user:
                raise NotFoundError("User not found.")

            event = (
                db.query(Event)
                .filter(Event.event_name == event_data["event_name"], Event.is_active, Event.user_id == user.id)
                .first()
            )

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

                db.add(event)
                db.commit()
                db.refresh(event)
            except Exception as e:
                raise ServiceError("Failed to create event.", e)

            return event

    def update_event(self, **event_data):
        with self.session_factory() as db:
            event = db.query(Event).filter(Event.id == event_data["id"], Event.user_id == event_data["user_id"]).first()

            if not event:
                raise NotFoundError("Event not found.")

            try:
                event.event_date = event_data.get("event_date", event.event_date)

                db.commit()
                db.refresh(event)
            except Exception as e:
                raise ServiceError("Failed to update event.", e)

            return event

    def soft_delete_event(self, **event_data):
        with self.session_factory() as db:
            event = (
                db.query(Event)
                .filter(Event.id == event_data["event_id"], Event.user_id == event_data["user_id"])
                .first()
            )

            if not event:
                raise NotFoundError("Event not found.")

            try:
                event.is_active = event_data.get("is_active", False)  # TODO: this is bug! it should always be false

                db.commit()
                db.refresh(event)
            except Exception as e:
                raise ServiceError("Failed to delete event.", e)
