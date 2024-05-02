import uuid

from server.database.database_manager import db
from server.database.models import User, Attendee, Event
from server.flask_app import FlaskApp
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.emails import EmailService, FakeEmailService
from server.services.shopify import ShopifyService, FakeShopifyService


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
        user = User.query.filter_by(email=user_data["email"]).first()

        if user:
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
        except ServiceError as e:
            db.session.rollback()
            raise ServiceError(e.message, e)
        except Exception as e:
            db.session.rollback()
            raise ServiceError("Failed to create user.", e)

        return user

    def get_user_by_id(self, user_id):
        return User.query.filter_by(id=user_id).first()

    def get_user_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def get_all_users(self):
        return User.query.all()

    def get_user_events(self, email):
        return Event.query.join(User, User.id == Event.user_id).filter(User.email == email).all()

    def update_user(self, user_data):
        user = User.query.filter_by(email=user_data["email"]).first()

        if not user:
            raise NotFoundError("User not found.")

        try:
            user.first_name = user_data.get("first_name")
            user.last_name = user_data.get("last_name")
            user.account_status = user_data.get("account_status")
            user.shopify_id = user_data.get("shopify_id")

            db.session.commit()
            db.session.refresh(user)
        except Exception as e:
            raise ServiceError("Failed to update user.", e)

        return user
