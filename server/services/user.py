import logging
import uuid

from server.database.database_manager import db
from server.database.models import User, Event, Attendee, Look, Discount, DiscountType
from server.flask_app import FlaskApp
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.emails import EmailService, FakeEmailService
from server.services.shopify import ShopifyService, FakeShopifyService

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        super().__init__()
        if FlaskApp.current().config["TMG_APP_TESTING"]:
            self.shopify_service = FakeShopifyService()
            self.email_service = FakeEmailService()
        else:
            self.shopify_service = ShopifyService()
            self.email_service = EmailService()

    def create_user(self, user_data):
        if User.query.filter_by(email=user_data["email"]).first():
            raise DuplicateError("User already exists with that email address.")

        try:
            shopify_customer_id = self.shopify_service.create_customer(
                user_data.get("first_name"), user_data["last_name"], user_data["email"]
            )["id"]

            user = User(
                id=uuid.uuid4(),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                email=user_data.get("email"),
                shopify_id=shopify_customer_id,
                account_status=user_data.get("account_status"),
            )

            db.session.add(user)

            if user.account_status:
                self.email_service.send_activation_url(user.email, shopify_customer_id)

            db.session.commit()
            db.session.refresh(user)
        except Exception as e:
            db.session.rollback()
            logger.exception(e)
            raise ServiceError("Failed to create user.")
        return user

    def get_user_by_shopify_id(self, shopify_id):
        return User.query.filter_by(shopify_id=shopify_id).first()

    def get_user_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def get_user_events(self, user_id):
        return Event.query.filter_by(user_id=user_id, is_active=True).all()

    def get_grooms_gift_paid_but_not_used_discounts(self, attendee_id):
        return Discount.query.filter(
            Discount.attendee_id == attendee_id,
            Discount.code != None,
            Discount.used == False,
            Discount.type == DiscountType.GROOM_GIFT,
        ).all()

    def get_user_discounts(self, user_id, event_id=None):
        groom_gift_discounts = (
            Discount.query.join(Attendee, Discount.attendee_id == Attendee.id)
            .join(User, Attendee.attendee_id == User.id)
            .filter(User.id == user_id, Discount.code != None)
            .all()
        )

        # if event_id:
        #     return (
        #         Discount.query.join(Attendee, Discount.attendee_id == Attendee.id)
        #         .join(User, Attendee.attendee_id == User.id)
        #         .filter(User.id == user_id, Attendee.event_id == event_id)
        #         .all()
        #     )
        # else:
        #     return (
        #         Discount.query.join(Attendee, Discount.attendee_id == Attendee.id)
        #         .join(User, Attendee.attendee_id == User.id)
        #         .filter(User.id == user_id)
        #         .all()
        #     )

    def get_user_invites(self, user_id):
        return (
            Event.query.join(Attendee, Event.id == Attendee.event_id)
            .filter(Attendee.attendee_id == user_id, Event.is_active)
            .all()
        )

    def get_user_looks(self, user_id):
        return Look.query.filter(Look.user_id == user_id).all()

    def update_user(self, user_id, user_data):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            raise NotFoundError("User not found.")

        try:
            user.first_name = user_data.get("first_name", user.first_name)
            user.last_name = user_data.get("last_name", user.last_name)
            user.account_status = user_data.get("account_status", user.account_status)
            user.shopify_id = user_data.get("shopify_id", user.shopify_id)

            db.session.commit()
            db.session.refresh(user)
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to update user.", e)

        return user
