import uuid

from server.database.database_manager import db
from server.database.models import Attendee, Event, User
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

    def get_attendee_user(self, attendee_id):
        return User.query.join(Attendee).filter(Attendee.id == attendee_id).first()

    def create_attendee(self, attendee_data):
        event = Event.query.filter(Event.id == attendee_data["event_id"], Event.is_active).first()

        if not event:
            raise NotFoundError("Event not found.")

        attendee_user = self.user_service.get_user_by_email(attendee_data["email"])

        if not attendee_user:
            disabled_user = {
                "first_name": attendee_data["first_name"],
                "last_name": attendee_data["last_name"],
                "email": attendee_data["email"],
                "account_status": False,
            }

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

    def apply_discounts(self, attendee_id, event_id, shopify_cart_id):
        from server.services.discount import DiscountService
        from server.services.event import EventService

        user_service = UserService()
        event_service = EventService()
        discount_service = DiscountService()

        discounts = user_service.get_grooms_gift_paid_but_not_used_discounts(attendee_id)

        num_attendees = event_service.get_num_attendees_for_event(event_id)

        if num_attendees >= 4:
            existing_discount = discount_service.get_group_discount_for_attendee(attendee_id)

            if not existing_discount:
                discount = discount_service.create_group_discount_for_attendee(attendee_id, event_id)
                discounts.append(discount)
            else:
                discounts.append(existing_discount)

        discounts = [discount for discount in discounts]

        if not discounts:
            return

        shopify_service = ShopifyService()
        shopify_service.apply_discount_codes_to_cart(shopify_cart_id, [discount.code for discount in discounts])
