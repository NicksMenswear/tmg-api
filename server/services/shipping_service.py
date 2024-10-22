import logging
import os
from datetime import timedelta, datetime
from typing import Dict, Any, Optional

from server.models.shipping_model import (
    ShippingPriceModel,
    ExpeditedShippingRateModel,
    FreeGroundShippingRateModel,
    StandardGroundShippingRateModel,
)
from server.services.attendee_service import AttendeeService
from server.services.event_service import EventService
from server.services.look_service import LookService
from server.services.webhook_handlers.shopify_order_webhook_handler import BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX

logger = logging.getLogger(__name__)

NUMBER_OF_WEEKS_FOR_EXPEDITED_SHIPPING: int = 6


class ShippingService:
    def __init__(self, look_service: LookService, attendee_service: AttendeeService, event_service: EventService):
        self.look_service = look_service
        self.attendee_service = attendee_service
        self.event_service = event_service

    def calculate_shipping_price(self, shipping_request: Dict[str, Any]) -> ShippingPriceModel:
        try:
            bundle_identifier_item = self.__find_shipping_bundle_identifier(shipping_request)

            if not bundle_identifier_item:
                return self.__calculate_shipping_price_model_by_checkout_items(shipping_request)

            look_model = self.look_service.find_look_by_product_id(bundle_identifier_item.get("product_id"))

            if not look_model:
                return self.__calculate_shipping_price_model_by_checkout_items(shipping_request)

            attendees = self.attendee_service.find_attendees_by_look_id(look_model.id)

            if not attendees:
                return self.__calculate_shipping_price_model_by_checkout_items(shipping_request)

            event_ids = set()

            for attendee in attendees:
                event_ids.add(attendee.event_id)

            events = self.event_service.get_events(list(event_ids))

            events_that_require_expedited_shipping = set()
            also_look_belong_to_future_event = False

            now = datetime.now()
            now_plus_6_weeks = now + timedelta(weeks=NUMBER_OF_WEEKS_FOR_EXPEDITED_SHIPPING)

            for event in events:
                if now <= event.event_at <= now_plus_6_weeks:
                    events_that_require_expedited_shipping.add(event)

                if event.event_at > now_plus_6_weeks:
                    also_look_belong_to_future_event = True

            if not events_that_require_expedited_shipping:
                return self.__calculate_shipping_price_model_by_checkout_items(shipping_request)
            else:
                if also_look_belong_to_future_event:
                    logger.error(
                        f"{os.getenv('STAGE')}: Look belongs to multiple events one of which requires expedited shipping: {look_model.id}",
                    )
                    return self.__calculate_shipping_price_model_by_checkout_items(shipping_request)
                else:
                    return ShippingPriceModel(rates=[ExpeditedShippingRateModel()])
        except Exception as e:
            logger.exception("Failed to calculate shipping rate", e)
            return ShippingPriceModel(rates=[StandardGroundShippingRateModel()])

    @staticmethod
    def __find_shipping_bundle_identifier(shipping_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        items = shipping_request.get("rate", {}).get("items", [])

        for item in items:
            if item.get("sku", "").startswith(BUNDLE_IDENTIFIER_PRODUCT_SKU_PREFIX):
                return item

        return None

    @staticmethod
    def __calculate_total_price(shipping_request: Dict[str, Any]) -> int:
        items = shipping_request.get("rate", {}).get("items", [])

        total_price = 0

        for item in items:
            total_price += item.get("price", 0) * item.get("quantity", 1)

        return total_price

    def __calculate_shipping_price_model_by_checkout_items(
        self, shipping_request: Dict[str, Any]
    ) -> ShippingPriceModel:
        total_price = self.__calculate_total_price(shipping_request)

        if total_price == 0:
            return ShippingPriceModel(rates=[FreeGroundShippingRateModel()])
        elif total_price >= 21000:
            return ShippingPriceModel(rates=[FreeGroundShippingRateModel()])
        else:
            return ShippingPriceModel(rates=[StandardGroundShippingRateModel()])
