import logging
import uuid
from typing import Any

from server.services.shopify_products_service import ShopifyProductService

logger = logging.getLogger(__name__)


class ShopifyWebhookProductHandler:
    def __init__(self, shopify_product_service: ShopifyProductService):
        self.__shopify_product_service = shopify_product_service

    def product_create(self, webhook_id: uuid.UUID, payload: dict[str, Any]) -> dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for product create: {webhook_id}")

        self.__shopify_product_service.upsert_product(payload.get("id"), payload)

        return {}

    def product_update(self, webhook_id: uuid.UUID, payload: dict[str, Any]) -> dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for product update: {webhook_id}")

        self.__shopify_product_service.upsert_product(payload.get("id"), payload)

        return {}

    def product_delete(self, webhook_id: uuid.UUID, payload: dict[str, Any]) -> dict[str, Any]:
        logger.debug(f"Handling Shopify webhook for product delete: {webhook_id}")

        self.__shopify_product_service.delete_product(payload.get("id"))

        return {}
