import uuid

from server.database.database_manager import db
from server.database.models import Event, User, Attendee, Look, Role
from server.services import ServiceError, NotFoundError, DuplicateError


class EventService:
    def get_event_by_id(self, event_id, enriched=False):
        event = Event.query.filter_by(id=event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        event = event.to_dict()

        if not enriched:
            return event

        event["attendees"] = []

        results = (
            db.session.query(Attendee, User, Look, Role)
            .join(Event, Event.id == Attendee.event_id)
            .join(User, User.id == Attendee.attendee_id)
            .outerjoin(Look, Look.id == Attendee.look_id)
            .outerjoin(Role, Role.id == Attendee.role)
            .filter(Event.id == event_id, Attendee.is_active)
            .all()
        )

        for attendee, user, look, role in results:
            attendee = {
                "id": attendee.id,
                "invite": attendee.invite,
                "pay": attendee.pay,
                "ship": attendee.ship,
                "size": attendee.size,
                "style": attendee.style,
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                },
                "look": None,
                "role": None,
            }

            if look:
                attendee["look"] = {
                    "id": look.id,
                    "look_name": look.look_name,
                    "product_specs": look.product_specs,
                }

            if role:
                attendee["role"] = {
                    "id": role.id,
                    "role_name": role.role_name,
                }

            event["attendees"].append(attendee)

        return event

    def create_event(self, event_data):
        user = User.query.filter_by(id=event_data["user_id"]).first()

        if not user:
            raise NotFoundError("User not found.")

        event = Event.query.filter(
            Event.event_name == event_data["event_name"], Event.is_active, Event.user_id == user.id
        ).first()

        if event:
            raise DuplicateError("Event with the same details already exists.")

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

    def update_event(self, event_id, event_data):
        event = Event.query.filter(Event.id == event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        try:
            event.event_date = event_data.get("event_date")
            event.event_name = event_data.get("event_name")

            db.session.commit()
            db.session.refresh(event)
        except Exception as e:
            raise ServiceError("Failed to update event.", e)

        return event

    def soft_delete_event(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        try:
            event.is_active = False

            db.session.commit()
            db.session.refresh(event)
        except Exception as e:
            raise ServiceError("Failed to deactivate event.", e)
