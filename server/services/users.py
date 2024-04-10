import uuid

from server.database.models import User
from server.services.error import ServiceError


class UserService:
    def __init__(self, session, shopify_service, email_service):
        self.db = session
        self.shopify_service = shopify_service
        self.email_service = email_service

    def create_user(self, first_name, last_name, email, account_status):
        try:
            shopify_customer_id = self.shopify_service.create_customer(first_name, last_name, email)["id"]
        except Exception as e:
            raise ServiceError("Failed to create shopify user.", e)

        try:
            user_id = uuid.uuid4()

            user = User(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                shopify_id=shopify_customer_id,
                account_status=account_status,
            )

            self.db.add(user)

            self.email_service.send_activation_url(user.email, shopify_customer_id)

            self.db.commit()
            self.db.refresh(user)
        except Exception as e:
            self.db.rollback()
            raise ServiceError("Failed to create user.", e)

        return user

    def get_user_by_email(self, email):
        return self.db.query(User).filter_by(email=email).first()

    def get_all_users(self):
        return self.db.query(User).all()

    def delete_user(self, email):
        user = self.get_user_by_email(email)

        if not user:
            return

        self.db.delete(user)
        self.db.commit()

    def update_user(self, email, updated_first_name, updated_last_name, updated_account_status, updated_shopify_id):
        user = self.get_user_by_email(email)

        user.first_name = updated_first_name
        user.last_name = updated_last_name
        user.account_status = updated_account_status
        user.shopify_id = updated_shopify_id

        self.db.commit()
        self.db.refresh(user)

        return user
