import logging
import uuid
from datetime import datetime
from operator import or_
from typing import List

from server.database.database_manager import db
from server.database.models import User, Attendee, Discount, DiscountType
from server.models.discount_model import DiscountModel
from server.models.user_model import CreateUserModel, UserModel, UpdateUserModel
from server.services import ServiceError, DuplicateError, NotFoundError
from server.services.email import AbstractEmailService
from server.services.shopify import AbstractShopifyService

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class UserService:
    def __init__(self, shopify_service: AbstractShopifyService, email_service: AbstractEmailService):
        self.shopify_service = shopify_service
        self.email_service = email_service

    def create_user(self, create_user: CreateUserModel) -> UserModel:
        user = User.query.filter_by(email=create_user.email).first()

        if user:
            raise DuplicateError("User already exists with that email address.")

        try:
            shopify_customer_id = self.shopify_service.create_customer(
                create_user.first_name, create_user.last_name, create_user.email
            )["id"]

            db_user = User(
                id=uuid.uuid4(),
                first_name=create_user.first_name,
                last_name=create_user.last_name,
                email=create_user.email,
                shopify_id=shopify_customer_id,
                account_status=create_user.account_status,
            )

            db.session.add(db_user)

            if db_user.account_status:
                self.email_service.send_activation_url(db_user.email, shopify_customer_id)

            db.session.commit()
            db.session.refresh(db_user)
        except Exception as e:
            db.session.rollback()
            logger.exception(e)
            raise ServiceError("Failed to create user.")

        return UserModel.from_orm(db_user)

    def get_user_by_email(self, email: str) -> UserModel:
        db_user = User.query.filter_by(email=email).first()

        if not db_user:
            raise NotFoundError("User not found.")

        return UserModel.from_orm(db_user)

    def get_user_for_attendee(self, attendee_id: uuid.UUID) -> UserModel:
        user = User.query.join(Attendee).filter(Attendee.id == attendee_id).first()

        if not user:
            raise NotFoundError("User not found.")

        return UserModel.from_orm(user)

    def get_gift_paid_but_not_used_discounts(self, attendee_id: uuid.UUID) -> List[DiscountModel]:
        return [
            DiscountModel.from_orm(discount)
            for discount in Discount.query.filter(
                Discount.attendee_id == attendee_id,
                Discount.shopify_discount_code != None,
                Discount.used == False,
                or_(Discount.type == DiscountType.GIFT, Discount.type == DiscountType.FULL_PAY),
            ).all()
        ]

    def update_user(self, user_id: uuid.UUID, update_user: UpdateUserModel) -> UserModel:
        user: User = User.query.filter_by(id=user_id).first()

        if not user:
            raise NotFoundError("User not found.")

        try:
            user.first_name = update_user.first_name
            user.last_name = update_user.last_name
            user.updated_at = datetime.now()

            db.session.commit()
            db.session.refresh(user)
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to update user.", e)

        return UserModel.from_orm(user)
