import logging

from server.services.attendee import AttendeeService
from server.services.discount import DiscountService
from server.services.shopify import ShopifyService
from server.services.user import UserService

logger = logging.getLogger(__name__)


class WebhookService:
    @staticmethod
    def handle_orders_paid(payload):
        items = payload.get("line_items")

        if not items or len(items) == 0:
            logger.error(f"Received paid order without items")
            return

        if len(items) == 1 and items[0].get("sku").startswith("GROOM-DISCOUNT-"):
            order_item = items[0]
            sku = order_item.get("sku")
            logger.debug(f"Found paid groom discount order with sku '{sku}'")
            WebhookService.handle_groom_discount(payload)

    @staticmethod
    def handle_groom_discount(payload):
        product = payload.get("line_items")[0]
        customer = payload.get("customer")

        shopify_product_id = product.get("product_id")
        shopify_customer_id = customer.get("id")

        logger.info(
            f"Handling groom discount for product_id '{shopify_product_id}' and customer_id '{shopify_customer_id}'"
        )

        discount_service = DiscountService()
        discounts = discount_service.get_discounts_for_product(shopify_product_id)

        shopify_service = ShopifyService()

        if not discounts:
            logger.error(f"No discounts found for product_id: {shopify_product_id}")
            return

        attendee_service = AttendeeService()
        user_service = UserService()
        groom_user = user_service.get_user_by_shopify_id(str(shopify_customer_id))

        for discount in discounts:
            attendee_user = attendee_service.get_attendee_user(discount.attendee_id)
            discount_response = shopify_service.create_discount_code(
                groom_user, attendee_user.shopify_id, discount.amount
            )
            discount_service.add_code_to_discount(
                discount.id, discount_response.get("shopify_discount_id"), discount_response.get("code")
            )
