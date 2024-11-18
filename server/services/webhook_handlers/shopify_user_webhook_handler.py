import logging
import re
import uuid
from typing import Any, Dict

from server.models.user_model import CreateUserModel, UpdateUserModel
from server.services import NotFoundError
from server.services.integrations.activecampaign_service import ActiveCampaignService
from server.services.order_service import OrderService
from server.services.size_service import SizeService
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


class ShopifyWebhookUserHandler:
    def __init__(
        self,
        user_service: UserService,
        size_service: SizeService,
        order_service: OrderService,
        activecampaign_service: ActiveCampaignService,
    ):
        self.user_service = user_service
        self.size_service = size_service
        self.order_service = order_service
        self.activecampaign_service = activecampaign_service

    def customer_update(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for customer update: {webhook_id}")

        shopify_id = str(payload.get("id"))
        email = payload.get("email").lower()
        first_name = payload.get("first_name") or self.__get_name_from_email(email)
        last_name = payload.get("last_name") or self.__get_name_from_email(email)
        state = payload.get("state")
        phone = payload.get("phone") or payload.get("default_address", {}).get("phone")

        try:
            user = self.user_service.get_user_by_shopify_id(shopify_id)  # first search by shopify_id
        except NotFoundError:
            try:
                # some legacy users don't have shopify_id so search by email
                user = self.user_service.get_user_by_email(email)
            except NotFoundError:
                user = None

        if not user:
            # User has signed up through social login, let's save them in our database
            updated_user = self.user_service.create_user(
                CreateUserModel(
                    shopify_id=str(shopify_id),
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    account_status=True if state == "enabled" else False,
                    phone_number=str(phone) if phone else None,
                )
            )

            latest_size = self.size_service.get_latest_size_for_user_by_email(email)

            if latest_size:
                self.user_service.set_size(updated_user.id, email, latest_size.created_at.isoformat())
                self.order_service.update_user_pending_orders_with_latest_measurements(latest_size)

            return updated_user.to_response()
        elif (
            str(shopify_id) != user.shopify_id
            or email != user.email
            or first_name != user.first_name
            or last_name != user.last_name
            or phone != user.phone_number
            or (state == "enabled" and not user.account_status)
        ):
            updated_user = self.user_service.update_user(
                user.id,
                UpdateUserModel(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    account_status=True if state == "enabled" else False,
                    shopify_id=str(shopify_id),
                    phone_number=str(phone) if phone else None,
                ),
                update_shopify=False,
            )

            return updated_user.to_response()
        else:
            return user.to_response()

    @staticmethod
    def __get_name_from_email(email: str) -> str:
        return re.sub(r"\W+", "", email.split("@")[0])
