import uuid

from server.database.models import Event
from server.services import ServiceError
from server.services.base import BaseService


class EventService(BaseService):
    def __init__(self, session_factory):
        super().__init__(session_factory)

    def create_event(self, **event_data):
        with self.session_factory() as db:
            # user = db.query(Event).filter_by(email=user_data["email"]).first()
            #
            # if user:
            #     raise DuplicateError("User already exists with that email address.")

            try:
                event = Event(
                    id=event_data.get("id", uuid.uuid4()),
                    event_name=event_data.get("event_name"),
                    event_date=event_data.get("event_date"),
                    user_id=event_data.get("user_id"),
                    is_active=event_data.get("is_active", True),
                )

                db.add(event)
                db.commit()
                db.refresh(event)
            except Exception as e:
                raise ServiceError("Failed to create event.", e)

            return event
