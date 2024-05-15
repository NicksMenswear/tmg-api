import logging

from server.services.shopify import ShopifyService

logger = logging.getLogger(__name__)


def apply_discounts(apply_discounts_request):
    from server.services.user import UserService

    user_service = UserService()
    discounts = user_service.get_user_discounts(apply_discounts_request["user_id"], apply_discounts_request["event_id"])
    discounts = [discount for discount in discounts if discount.code]

    if not discounts:
        return "{}", 200

    shopify_service = ShopifyService()
    response = shopify_service.apply_discount_codes_to_cart(
        apply_discounts_request["shopify_cart_id"], [discount.code for discount in discounts]
    )

    logger.info(f"Discount codes applied to cart {apply_discounts_request}")
    logger.info(f"Response body: {response}")

    # get groom discounts for the customer

    return "{}", 200
