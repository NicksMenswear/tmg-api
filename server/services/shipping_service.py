import logging
from datetime import timedelta, datetime
from typing import Dict, Any, Optional

from server.models.shipping_model import (
    ShippingPriceModel,
    ExpeditedShippingRateModel,
    GroundShippingRateModel,
)
from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.look_service import LookService
from server.services.webhook_handlers.shopify_order_webhook_handler import BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX

logger = logging.getLogger(__name__)

NUMBER_OF_WEEKS_FOR_EXPEDITED_SHIPPING: int = 6


# noinspection PyMethodMayBeStatic
class ShippingService:
    def __init__(self, look_service: LookService, attendee_service: AttendeeService, event_service: EventService):
        self.look_service = look_service
        self.attendee_service = attendee_service
        self.event_service = event_service

    def calculate_shipping_price(self, shipping_request: Dict[str, Any]) -> ShippingPriceModel:
        try:
            bundle_identifier_item = self.__find_shipping_bundle_identifier(shipping_request)

            if not bundle_identifier_item:
                return ShippingPriceModel(rates=[GroundShippingRateModel()])

            look_model = self.look_service.find_look_by_product_id(bundle_identifier_item.get("product_id"))

            if not look_model:
                return ShippingPriceModel(rates=[GroundShippingRateModel()])

            attendees = self.attendee_service.find_attendees_by_look_id(look_model.id)

            if not attendees:
                return ShippingPriceModel(rates=[GroundShippingRateModel()])

            event_id = attendees[0].event_id

            event = self.event_service.get_event_by_id(event_id)

            if event.event_at < datetime.now() + timedelta(weeks=NUMBER_OF_WEEKS_FOR_EXPEDITED_SHIPPING):
                return ShippingPriceModel(rates=[ExpeditedShippingRateModel()])
        except Exception as e:
            logger.exception("Failed to calculate shipping rate", e)
            return ShippingPriceModel(rates=[GroundShippingRateModel()])

        return ShippingPriceModel(rates=[GroundShippingRateModel()])

    def __find_shipping_bundle_identifier(self, shipping_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        items = shipping_request.get("rate", {}).get("items", [])

        for item in items:
            if item.get("sku", "").startswith(BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX):
                return item

        return None
