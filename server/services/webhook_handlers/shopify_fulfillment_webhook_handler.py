import logging
import uuid
from typing import Any, Dict

from server.services.integrations.sms_service import AbstractSmsService
from server.services.order_service import (
    OrderService,
)
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


class ShopifyWebhookFulfillmentHandler:
    def __init__(
        self,
        user_service: UserService,
        order_service: OrderService,
        sms_service: AbstractSmsService,
    ):
        self.user_service = user_service
        self.order_service = order_service
        self.sms_service = sms_service

    def fulfillment_create(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for fulfillment create: {webhook_id}")

        shopify_order_id = str(payload.get("order_id"))
        order = self.order_service.get_order_by_shopify_id(uuid.UUID(shopify_order_id))
        user = self.user_service.get_user_by_id(order.user_id)

        self.__save_tracking(order, payload)
        self.__sms_tracking(user, payload)

    def __save_tracking(self, order, payload):
        order.outbound_tracking = payload.get("tracking_number")
        self.order_service.update_order(order)

    def __sms_tracking(self, user, payload):
        if not user.phone_number:
            return
        if not user.sms_consent:
            return
        if not payload.get("tracking_number"):
            return
        self.sms_service.send_tracking(user.phone_number, payload.get("tracking_number"))
