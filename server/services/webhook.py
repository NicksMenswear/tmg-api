import logging
import random

from server.services.attendee import AttendeeService
from server.services.discount import DiscountService
from server.services.shopify import ShopifyService
from server.services.user import UserService

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(
        self,
        user_service: UserService,
        attendee_service: AttendeeService,
        discount_service: DiscountService,
        shopify_service: ShopifyService,
    ):
        self.user_service = user_service
        self.attendee_service = attendee_service
        self.discount_service = discount_service
        self.shopify_service = shopify_service

    def handle_orders_paid(self, payload):
        items = payload.get("line_items")

        if not items or len(items) == 0:
            logger.error(f"Received paid order without items")
            return

        if len(items) == 1 and items[0].get("sku").startswith("GROOM-DISCOUNT-"):
            order_item = items[0]
            sku = order_item.get("sku")
            logger.debug(f"Found paid groom discount order with sku '{sku}'")
            self.handle_groom_gift_discount(payload)
            return

        if len(payload.get("discount_codes")) > 0:
            self.handle_used_discount_code(payload)

    def handle_groom_gift_discount(self, payload):
        product = payload.get("line_items")[0]
        customer = payload.get("customer")

        shopify_product_id = product.get("product_id")
        shopify_customer_id = customer.get("id")

        logger.info(
            f"Handling groom discount for product_id '{shopify_product_id}' and customer_id '{shopify_customer_id}'"
        )

        discounts = self.discount_service.get_groom_gift_discount_intents_for_product(shopify_product_id)

        shopify_service = self.shopify_service

        if not discounts:
            logger.error(f"No discounts found for product_id: {shopify_product_id}")
            return

        groom_user = self.user_service.get_user_by_shopify_id(str(shopify_customer_id))

        for discount in discounts:
            attendee_user = self.attendee_service.get_attendee_user(discount.attendee_id)

            code = f"GROOM-GIFT-{discount.amount}-OFF-{random.randint(100000, 9999999)}"

            discount_response = shopify_service.create_discount_code(
                code,
                code,
                attendee_user.shopify_id,
                discount.amount,
            )

            self.discount_service.add_code_to_discount(
                discount.id, discount_response.get("shopify_discount_id"), discount_response.get("code")
            )

    def handle_used_discount_code(self, payload):
        discount_codes = payload.get("discount_codes")

        if not discount_codes:
            logger.error(f"No discount codes found in payload")
            return

        for discount_code in discount_codes:
            shopify_discount_code = discount_code.get("code")

            discount = self.discount_service.mark_discount_by_shopify_code_as_paid(shopify_discount_code)

            if discount:
                logger.info(f"Marked discount with code '{shopify_discount_code}' with id '{discount.id}' as paid")
