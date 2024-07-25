import logging
import uuid
from typing import Any, Dict

from server.models.user_model import CreateUserModel, UpdateUserModel
from server.services import NotFoundError
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


class ShopifyWebhookUserHandler:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def customer_update(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for customer update: {webhook_id}")

        shopify_id = payload.get("id")
        email = payload.get("email")
        first_name = payload.get("first_name")
        last_name = payload.get("last_name")
        state = payload.get("state")
        phone = payload.get("phone")

        try:
            user = self.user_service.get_user_by_email(email)
        except NotFoundError:
            user = None

        if not user:
            updated_user = self.user_service.create_user(
                CreateUserModel(
                    shopify_id=str(shopify_id),
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    account_status=True if state == "enabled" else False,
                    phone_number=str(phone),
                )
            )

            return updated_user.to_response()
        elif (
            str(shopify_id) != user.shopify_id
            or email != user.email
            or first_name != user.first_name
            or last_name != user.last_name
            or str(phone) != user.phone_number
            or (state == "enabled" and not user.account_status)
        ):
            updated_user = self.user_service.update_user(
                user.id,
                UpdateUserModel(
                    first_name=first_name,
                    last_name=last_name,
                    account_status=True if state == "enabled" else False,
                    shopify_id=str(shopify_id),
                    phone_number=str(phone) if phone else None,
                ),
            )

            return updated_user.to_response()
        else:
            return user.to_response()
