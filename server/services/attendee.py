import uuid

from server.database.database_manager import db
from server.database.models import Attendee, Event
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.base import BaseService
from server.services.user import UserService
from server.flask_app import FlaskApp


class AttendeeService(BaseService):
    def __init__(self, shopify_service=None, email_service=None):
        super().__init__()

        self.user_service = UserService()
        self.shopify_service = shopify_service or FlaskApp.current().shopify_service
        self.email_service = email_service or FlaskApp.current().email_service

    def create_attendee(self, **attendee_data):
        user = self.user_service.get_user_by_email(attendee_data["email"])

        if not user:
            disabled_user = {**attendee_data, "account_status": False}

            try:
                user = self.user_service.create_user(**disabled_user)
            except Exception as e:
                raise ServiceError("Failed to create user for attendee.", e)

        attendee = Attendee.query.filter(
            Attendee.event_id == attendee_data["event_id"],
            Attendee.attendee_id == user.id,
            Attendee.is_active,
        ).first()

        if attendee:
            raise DuplicateError("Attendee already exists.")
        else:
            try:
                new_attendee = Attendee(
                    id=uuid.uuid4(),
                    attendee_id=user.id,
                    event_id=attendee_data.get("event_id"),
                    style=attendee_data.get("style"),
                    invite=attendee_data.get("invite"),
                    pay=attendee_data.get("pay"),
                    size=attendee_data.get("size"),
                    ship=attendee_data.get("ship"),
                    role=attendee_data.get("role"),
                    is_active=attendee_data.get("is_active", True),
                )

                db.session.add(new_attendee)
                db.session.commit()
                db.session.refresh(new_attendee)
            except Exception as e:
                raise ServiceError("Failed to create attendee.", e)

            return new_attendee

    def get_attendee_by_id(self, attendee_id):
        attendee = Attendee.query.filter(Attendee.id == attendee_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        return attendee

    def get_attendee_by_id(self, attendee_id):
        attendee = Attendee.query.filter(Attendee.id == attendee_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        return attendee

    def get_attendee_event(self, email, event_id):
        user = self.user_service.get_user_by_email(email)

        if not user:
            raise NotFoundError("Attendee user not found.")

        event = (
            Event.query.join(Attendee, Event.id == Attendee.event_id)
            .filter(
                Event.id == event_id,
                Attendee.attendee_id == user.id,
                Event.is_active == True,
                Attendee.is_active == True,
            )
            .first()
        )

        if not event:
            raise NotFoundError("No active event found")

        return event

    def get_attendees_for_event_by_id(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()

        if not event:
            raise NotFoundError("Event not found.")

        attendees = (
            Attendee.query.join(Event, Attendee.event_id == Event.id)
            .filter(Attendee.event_id == event_id, Attendee.is_active == True, Event.is_active == True)
            .all()
        )

        enriched_attendees = []

        for attendee in attendees:
            attendee_user = self.user_service.get_user_by_id(attendee.attendee_id)

            data = {
                "id": attendee.id,
                "first_name": attendee_user.first_name,
                "last_name": attendee_user.last_name,
                "email": attendee_user.email,
                "account_status": attendee_user.account_status,
                "event_id": attendee.event_id,
                "style": attendee.style,
                "invite": attendee.invite,
                "pay": attendee.pay,
                "size": attendee.size,
                "ship": attendee.ship,
                "is_Active": attendee.is_active,
                "role": attendee.role,
            }

            enriched_attendees.append(data)

        return enriched_attendees

    def update_attendee(self, **attendee_data):
        attendee_user = self.user_service.get_user_by_email(attendee_data["email"])

        if not attendee_user:
            raise NotFoundError("Attendee user not found.")

        attendee = (
            Attendee.query.join(Event, Attendee.event_id == Event.id)
            .filter(Attendee.event_id == attendee_data["event_id"], Attendee.attendee_id == attendee_user.id)
            .first()
        )

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.style = attendee_data["style"]
        attendee.invite = attendee_data["invite"]
        attendee.pay = attendee_data["pay"]
        attendee.size = attendee_data["size"]
        attendee.ship = attendee_data["ship"]
        attendee.role = attendee_data["role"]

        try:
            db.session.commit()
            db.session.refresh(attendee)
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

        return attendee

    def soft_delete_attendee(self, **attendee_data):
        attendee_user = self.user_service.get_user_by_email(attendee_data["email"])

        if not attendee_user:
            raise NotFoundError("Attendee user not found.")

        attendee = Attendee.query.filter(
            Attendee.attendee_id == attendee_user.id, Attendee.event_id == attendee_data["event_id"]
        ).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.is_active = attendee_data["is_active"]

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to delete attendee.", e)
