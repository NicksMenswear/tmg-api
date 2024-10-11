import uuid
from typing import Any, Dict


# noinspection PyUnusedLocal
class ShopifyWebhookCheckoutHandler:
    @staticmethod
    def checkout_create(webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}

    @staticmethod
    def checkout_update(webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}

    @staticmethod
    def checkout_delete(webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}
