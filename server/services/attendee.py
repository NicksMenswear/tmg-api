import uuid

from server.database.database_manager import db
from server.database.models import Attendee, Event
from server.flask_app import FlaskApp
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.emails import EmailService, FakeEmailService
from server.services.shopify import ShopifyService, FakeShopifyService
from server.services.user import UserService


class AttendeeService:
    def __init__(self):
        super().__init__()
        self.user_service = UserService()

        if FlaskApp.current().config["TMG_APP_TESTING"]:
            self.shopify_service = FakeShopifyService()
            self.email_service = FakeEmailService()
        else:
            self.shopify_service = ShopifyService()
            self.email_service = EmailService()

    def get_attendee_by_id(self, attendee_id):
        return Attendee.query.filter(Attendee.id == attendee_id).first()

    def create_attendee(self, attendee_data):
        event = Event.query.filter(Event.id == attendee_data["event_id"], Event.is_active).first()

        if not event:
            raise NotFoundError("Event not found.")

        attendee_user = self.user_service.get_user_by_email(attendee_data["email"])

        if not attendee_user:
            disabled_user = {**attendee_data, "account_status": False}

            try:
                attendee_user = self.user_service.create_user(disabled_user)
            except Exception as e:
                raise ServiceError("Failed to create user for attendee.", e)

        attendee = Attendee.query.filter(
            Attendee.event_id == attendee_data["event_id"],
            Attendee.attendee_id == attendee_user.id,
            Attendee.is_active,
        ).first()

        if attendee:
            raise DuplicateError("Attendee already exists.")
        else:
            try:
                new_attendee = Attendee(
                    id=uuid.uuid4(),
                    attendee_id=attendee_user.id,
                    event_id=attendee_data.get("event_id"),
                    style=attendee_data.get("style"),
                    invite=attendee_data.get("invite"),
                    pay=attendee_data.get("pay"),
                    size=attendee_data.get("size"),
                    ship=attendee_data.get("ship"),
                    role=attendee_data.get("role"),
                    look_id=attendee_data.get("look_id"),
                    is_active=attendee_data.get("is_active", True),
                )

                db.session.add(new_attendee)
                db.session.commit()
                db.session.refresh(new_attendee)
            except Exception as e:
                raise ServiceError("Failed to create attendee.", e)

            return new_attendee

    def update_attendee(self, attendee_id, attendee_data):
        attendee = Attendee.query.filter(Attendee.id == attendee_id, Attendee.is_active).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.style = attendee_data.get("style")
        attendee.invite = attendee_data.get("invite")
        attendee.pay = attendee_data.get("pay")
        attendee.size = attendee_data.get("size")
        attendee.ship = attendee_data.get("ship")
        attendee.role = attendee_data.get("role")
        attendee.look_id = attendee_data.get("look_id")

        try:
            db.session.commit()
            db.session.refresh(attendee)
        except Exception as e:
            raise ServiceError("Failed to update attendee.", e)

        return attendee

    def soft_delete_attendee(self, attendee_id):
        attendee = Attendee.query.filter(Attendee.id == attendee_id).first()

        if not attendee:
            raise NotFoundError("Attendee not found.")

        attendee.is_active = False

        try:
            db.session.commit()
        except Exception as e:
            raise ServiceError("Failed to deactivate attendee.", e)
