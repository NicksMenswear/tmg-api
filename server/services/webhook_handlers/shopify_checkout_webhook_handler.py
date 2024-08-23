import logging
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ShopifyWebhookCheckoutHandler:
    def checkout_create(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}

    def checkout_update(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}

    def checkout_delete(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}
