import logging
from datetime import timedelta, datetime
from typing import Dict, Any, Optional

from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.look_service import LookService
from server.services.webhook_handlers.shopify_order_webhook_handler import BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX

logger = logging.getLogger(__name__)

NUMBER_OF_WEEKS_FOR_EXPEDITED_SHIPPING = 6


class ShippingService:
    def __init__(self, look_service: LookService, attendee_service: AttendeeService, event_service: EventService):
        self.look_service = look_service
        self.attendee_service = attendee_service
        self.event_service = event_service

    def calculate_shipping_price(self, shipping_request: Dict[str, Any]) -> str:
        try:
            bundle_identifier_item = self.__find_shipping_bundle_identifier(shipping_request)

            if not bundle_identifier_item:
                return "0"

            look_model = self.look_service.find_look_by_product_id(bundle_identifier_item.get("product_id"))

            if not look_model:
                return "0"

            attendees = self.attendee_service.find_attendees_by_look_id(look_model.id)

            if not attendees:
                return "0"

            event_id = attendees[0].event_id

            event = self.event_service.get_event_by_id(event_id)

            if event.event_at < datetime.now() + timedelta(weeks=NUMBER_OF_WEEKS_FOR_EXPEDITED_SHIPPING):
                return "4500"
        except Exception as e:
            logger.exception("Failed to calculate shipping rate", e)
            return "0"

        return "0"

    def __find_shipping_bundle_identifier(self, shipping_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        items = shipping_request.get("rate", {}).get("items", [])

        for item in items:
            if item.get("sku", "").startswith(BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX):
                return item

        return None
