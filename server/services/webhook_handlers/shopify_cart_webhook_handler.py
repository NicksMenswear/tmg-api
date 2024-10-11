import uuid
from typing import Any, Dict


# noinspection PyUnusedLocal
class ShopifyWebhookCartHandler:
    @staticmethod
    def cart_create(webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}

    @staticmethod
    def cart_update(webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}
