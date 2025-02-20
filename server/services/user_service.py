import logging
import uuid
from datetime import datetime
from typing import List, Optional, Set

from sqlalchemy import func, select, and_

from server.database.database_manager import db
from server.database.models import User, Attendee, Discount, DiscountType
from server.flask_app import FlaskApp
from server.models.discount_model import DiscountModel
from server.models.user_model import CreateUserModel, UserModel, UpdateUserModel
from server.services import BadRequestError, ServiceError, DuplicateError, NotFoundError
from server.services.integrations.activecampaign_service import AbstractActiveCampaignService
from server.services.integrations.email_service import AbstractEmailService
from server.services.integrations.shopify_service import AbstractShopifyService, ShopifyService

logger = logging.getLogger(__name__)

MAX_NAME_LENGTH = 63


class UserService:
    def __init__(
        self,
        shopify_service: AbstractShopifyService,
        email_service: Optional[AbstractEmailService] = None,
        activecampaign_service: Optional[AbstractActiveCampaignService] = None,
    ):
        self.shopify_service = shopify_service
        self.email_service = email_service
        self.activecampaign_service = activecampaign_service

    def create_user(self, create_user: CreateUserModel, send_activation_email: bool = False) -> UserModel:
        user = (
            db.session.execute(select(User).where(func.lower(User.email) == create_user.email.lower()))
            .scalars()
            .first()
        )
        first_name = None if not create_user.first_name else create_user.first_name[:MAX_NAME_LENGTH]
        last_name = None if not create_user.last_name else create_user.last_name[:MAX_NAME_LENGTH]

        if user:
            raise DuplicateError("User already exists with that email address.")

        if create_user.shopify_id:
            shopify_customer_id = create_user.shopify_id
        else:
            try:
                shopify_customer_id = self.shopify_service.create_customer(
                    first_name, last_name, create_user.email
                ).get_id()
            except DuplicateError as e:
                # If the user already exists in Shopify, we should still create a user in our database
                logger.debug(e)

                shopify_customer_id = str(self.shopify_service.get_customer_by_email(create_user.email).get_id())

        try:
            db_user = User(
                first_name=first_name,
                last_name=last_name,
                email=create_user.email.lower(),
                shopify_id=str(shopify_customer_id),
                phone_number=create_user.phone_number,
                sms_consent=create_user.sms_consent,
                email_consent=create_user.email_consent,
                account_status=create_user.account_status,
                meta=create_user.meta,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.session.add(db_user)
            db.session.commit()
            db.session.refresh(db_user)

            user_model = UserModel.model_validate(db_user)

            self.__link_new_user_to_his_latest_sizing(db_user)

            if send_activation_email:
                self.email_service.send_activation_email(user_model)

            # Tracking # TODO: async
            events = ["Signed Up"]

            if user_model.account_status:
                events.append("Activated Account")

            self.activecampaign_service.sync_contact(
                email=user_model.email,
                first_name=user_model.first_name,
                last_name=user_model.last_name,
                phone=user_model.phone_number,
                events=events,
            )

            return user_model
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def get_user_by_id(user_id: uuid.UUID) -> UserModel:
        db_user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

        if not db_user:
            raise NotFoundError("User not found.")

        return UserModel.model_validate(db_user)

    @staticmethod
    def get_user_by_email(email: str) -> UserModel:
        db_user = db.session.execute(select(User).where(func.lower(User.email) == email.lower())).scalars().first()

        if not db_user:
            raise NotFoundError("User not found.")

        return UserModel.model_validate(db_user)

    @staticmethod
    def get_user_by_shopify_id(shopify_id: str) -> UserModel:
        db_user = db.session.execute(select(User).where(User.shopify_id == shopify_id)).scalar_one_or_none()

        if not db_user:
            raise NotFoundError("User not found.")

        return UserModel.model_validate(db_user)

    @staticmethod
    def get_user_for_attendee(attendee_id: uuid.UUID) -> UserModel:
        user = db.session.execute(select(User).join(Attendee).where(Attendee.id == attendee_id)).scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found.")

        return UserModel.model_validate(user)

    @staticmethod
    def get_gift_paid_but_not_used_discounts(attendee_id: uuid.UUID) -> List[DiscountModel]:
        discounts = (
            db.session.execute(
                select(Discount).where(
                    and_(
                        Discount.attendee_id == attendee_id,
                        Discount.shopify_discount_code != None,
                        Discount.used == False,
                        Discount.type == DiscountType.GIFT,
                    )
                )
            )
            .scalars()
            .all()
        )

        return [DiscountModel.model_validate(discount) for discount in discounts]

    def update_user(self, user_id: uuid.UUID, update_user: UpdateUserModel, update_shopify=True) -> UserModel:
        user: User = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found.")

        first_name = update_user.first_name or user.first_name
        last_name = update_user.last_name or user.last_name
        email = update_user.email or user.email
        account_status = update_user.account_status if update_user.account_status is not None else user.account_status
        activated_account = account_status and not user.account_status
        sms_consent = update_user.sms_consent if update_user.sms_consent is not None else user.sms_consent
        email_consent = update_user.email_consent if update_user.email_consent is not None else user.email_consent

        user.first_name = first_name[:MAX_NAME_LENGTH]
        user.last_name = last_name[:MAX_NAME_LENGTH]
        user.email = email.lower()
        if update_user.phone_number and update_user.phone_number != user.phone_number:
            new_phone_number = update_user.phone_number
            user.phone_number = new_phone_number
        else:
            new_phone_number = None
        user.account_status = account_status
        user.sms_consent = sms_consent
        user.email_consent = email_consent
        user.updated_at = datetime.now()

        try:
            if update_shopify:
                self.shopify_service.update_customer(
                    ShopifyService.customer_gid(int(user.shopify_id)),
                    user.first_name,
                    user.last_name,
                    user.email,
                    new_phone_number,
                )

            db.session.commit()
            db.session.refresh(user)
        except BadRequestError as e:
            logger.exception(e)
            raise
        except Exception as e:
            logger.exception(e)

        # Tracking # TODO: async
        events = []

        if activated_account:
            events.append("Activated Account")

        self.activecampaign_service.sync_contact(
            user.email, user.first_name, user.last_name, phone=user.phone_number, events=events
        )

        return UserModel.model_validate(user)

    def update_customer_with_latest_sizing(self, user_id: uuid.UUID, email: str, latest_sizing: str) -> None:
        if user_id:
            user = self.get_user_by_id(user_id)
        else:
            try:
                user = self.get_user_by_email(email)
            except NotFoundError:
                logger.info(f"User {email} does not exist yet found.")
                user = None

        if not user:
            return

        try:
            self.shopify_service.update_customer(
                ShopifyService.customer_gid(int(user.shopify_id)), latest_sizing=latest_sizing
            )
        except ServiceError:
            logger.error(f"Failed to update user {user.email} size in Shopify.")

    def generate_activation_url(self, user_id: uuid.UUID) -> str:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

        if not user or not user.shopify_id:
            raise ServiceError("User does not have a Shopify ID.")

        return self.shopify_service.get_account_activation_url(int(user.shopify_id))

    @staticmethod
    def add_meta_tag(user_id: uuid.UUID, tags: Set[str]) -> None:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found.")

        new_meta = user.meta.copy()
        new_meta["tags"] = list(set(user.meta.get("tags", [])) | tags)
        user.meta = new_meta

        try:
            db.session.commit()
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to add tag to user.", e)

    @staticmethod
    def remove_meta_tag(user_id: uuid.UUID, tags: Set[str]) -> None:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found.")

        new_meta = user.meta.copy()
        new_meta["tags"] = list(set(user.meta.get("tags", [])) - tags)
        user.meta = new_meta

        try:
            db.session.commit()
        except Exception as e:
            logger.exception(e)
            raise ServiceError("Failed to remove tag from user.", e)

    @staticmethod
    def __link_new_user_to_his_latest_sizing(user: User):
        size_service = FlaskApp.current().size_service
        order_service = FlaskApp.current().order_service

        latest_size = size_service.get_latest_size_for_user_by_id_or_email(user.id, user.email)

        if not latest_size:
            return

        size_service.associate_sizing_that_has_email_with_user(user.email, user.id)
        order_service.update_user_pending_orders_with_latest_measurements(latest_size)
