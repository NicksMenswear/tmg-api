import logging
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class ShopifyWebhookCartHandler:
    def cart_create(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}

    def cart_update(self, webhook_id: uuid.UUID, payload: Dict[str, Any]) -> Dict[str, Any]:
        # noop
        return {}
