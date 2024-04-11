import uuid

from flask import current_app
from server.database.models import User
from server.services import ServiceError, DuplicateError, NotFoundError


class UserService:
    def __init__(self, session_factory, shopify_service=None, email_service=None):
        self.session_factory = session_factory
        self.shopify_service = shopify_service or current_app.shopify_service
        self.email_service = email_service or current_app.email_service

    def create_user(self, **kwargs):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=kwargs["email"]).first()

            if user:
                raise DuplicateError("User already exists with that email address.")

            try:
                shopify_customer_id = self.shopify_service.create_customer(
                    kwargs.get("first_name"), kwargs["last_name"], kwargs["email"]
                )["id"]

                user = User(
                    id=uuid.uuid4(),
                    first_name=kwargs.get("first_name"),
                    last_name=kwargs.get("last_name"),
                    email=kwargs.get("email"),
                    shopify_id=shopify_customer_id,
                    account_status=kwargs.get("account_status"),
                )

                db.add(user)

                self.email_service.send_activation_url(user.email, shopify_customer_id)

                db.commit()
                db.refresh(user)
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

    def update_user(self, **kwargs):
        with self.session_factory() as db:
            user = db.query(User).filter_by(email=kwargs["email"]).first()

            if not user:
                raise NotFoundError("User not found.")

            try:
                user.first_name = kwargs.get("first_name")
                user.last_name = kwargs.get("last_name")
                user.account_status = kwargs.get("account_status")
                user.shopify_id = kwargs.get("shopify_id")

                db.commit()
                db.refresh(user)
            except Exception as e:
                raise ServiceError("Failed to update user.", e)

            return user
