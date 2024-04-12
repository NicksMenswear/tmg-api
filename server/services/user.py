import uuid

from flask import current_app

from server.database.models import User
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.base import BaseService


class UserService(BaseService):
    def __init__(self, session_factory, shopify_service=None, email_service=None):
        super().__init__(session_factory)

        self.shopify_service = shopify_service or current_app.shopify_service
        self.email_service = email_service or current_app.email_service

    def create_user(self, **user_data):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=user_data["email"]).first()

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

                db.add(user)

                self.email_service.send_activation_url(user.email, shopify_customer_id)

                db.commit()
                db.refresh(user)
            except ServiceError as e:
                db.rollback()
                raise ServiceError(e.message, e)
            except Exception as e:
                db.rollback()
                raise ServiceError("Failed to create user.", e)

            return user

    def get_user_by_email(self, email):
        with self.session_factory() as db:
            return db.query(User).filter_by(email=email).first()

    def get_all_users(self):
        with self.session_factory() as db:
            return db.query(User).all()

    def update_user(self, **user_data):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=user_data["email"]).first()

            if not user:
                raise NotFoundError("User not found.")

            try:
                user.first_name = user_data.get("first_name")
                user.last_name = user_data.get("last_name")
                user.account_status = user_data.get("account_status")
                user.shopify_id = user_data.get("shopify_id")

                db.commit()
                db.refresh(user)
            except Exception as e:
                raise ServiceError("Failed to update user.", e)

            return user
