import logging
import random

from server.services.attendee import AttendeeService
from server.services.discount import (
    DiscountService,
    GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX,
    GROOM_GIFT_DISCOUNT_CODE_PREFIX,
)
from server.services.look import LookService
from server.services.shopify import ShopifyService
from server.services.user import UserService

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(
        self,
        user_service: UserService,
        attendee_service: AttendeeService,
        discount_service: DiscountService,
        look_service: LookService,
        shopify_service: ShopifyService,
    ):
        self.user_service = user_service
        self.attendee_service = attendee_service
        self.discount_service = discount_service
        self.look_service = look_service
        self.shopify_service = shopify_service

    def __error(self, message):
        return {"errors": message}

    def handle_orders_paid(self, payload):
        items = payload.get("line_items")

        if not items or len(items) == 0:
            logger.debug(f"Received paid order without items")
            return self.__error("No items in order")

        if (
            len(items) == 1
            and items[0].get("sku")
            and items[0].get("sku").startswith(GROOM_DISCOUNT_VIRTUAL_PRODUCT_PREFIX)
        ):
            sku = items[0].get("sku")
            logger.debug(f"Found paid groom discount order with sku '{sku}'")
            return self.handle_groom_gift_discount(payload)

        if len(payload.get("discount_codes")) > 0:
            return self.handle_used_discount_code(payload)

    def handle_groom_gift_discount(self, payload):
        product = payload.get("line_items")[0]
        customer = payload.get("customer")

        shopify_product_id = product.get("product_id")
        shopify_customer_id = customer.get("id")

        logger.info(
            f"Handling groom discount for product_id '{shopify_product_id}' and customer_id '{shopify_customer_id}'"
        )

        try:
            self.shopify_service.archive_product(shopify_product_id)
        except Exception as e:
            logger.error(f"Error archiving product with id '{shopify_product_id}': {e}")  # log but proceed

        discounts = self.discount_service.get_gift_discount_intents_for_product(shopify_product_id)

        if not discounts:
            logger.error(f"No discounts found for product_id: {shopify_product_id}")
            return self.__error("No discounts found for product")

        discounts_codes = []

        for discount in discounts:
            attendee_user = self.user_service.get_user_for_attendee(discount.attendee_id)
            attendee = self.attendee_service.get_attendee_by_id(discount.attendee_id)

            if not attendee.look_id:
                logger.error(f"No look associated for attendee '{attendee.id}' can't create discount code")
                return self.__error(f"No look associated for attendee '{attendee.id}' can't create discount code")

            look = self.look_service.get_look_by_id(attendee.look_id)

            if not look or not look.product_specs or len(look.product_specs.get("variants", [])) == 0:
                logger.error(f"No shopify variants founds for look {look.id}. Can't create discount code")
                return self.__error(f"No shopify variants founds for look {look.id}. Can't create discount code")

            code = f"{GROOM_GIFT_DISCOUNT_CODE_PREFIX}-{discount.amount}-OFF-{random.randint(100000, 9999999)}"

            discount_response = self.shopify_service.create_discount_code(
                code,
                code,
                attendee_user.shopify_id,
                discount.amount,
                look.product_specs.get("variants"),
            )

            self.discount_service.add_code_to_discount(
                discount.id,
                discount_response.get("shopify_discount_id"),
                discount_response.get("shopify_discount_code"),
            )

            discounts_codes.append(discount_response.get("shopify_discount_code"))

        return {"discount_codes": discounts_codes}

    def handle_used_discount_code(self, payload):
        discount_codes = payload.get("discount_codes", [])

        if len(discount_codes) == 0:
            logger.debug(f"No discount codes found in payload")
            return {}

        used_discount_codes = []

        for discount_code in discount_codes:
            shopify_discount_code = discount_code.get("code")

            discount = self.discount_service.mark_discount_by_shopify_code_as_paid(shopify_discount_code)

            if discount:
                used_discount_codes.append(shopify_discount_code)
                logger.info(f"Marked discount with code '{shopify_discount_code}' with id '{discount.id}' as paid")

        return used_discount_codes
