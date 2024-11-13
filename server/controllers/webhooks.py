import logging

from connexion import request

from server.controllers.util import hmac_webhook_verification
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_webhook_verification
def shopify_webhook(payload):
    topic = request.headers.get("X-Shopify-Topic")

    if not topic:
        logger.error("Received Shopify webhook without topic")
        return "Bad Request", 400

    logger.info(f"Received Shopify webhook with topic: {topic}")

    app = FlaskApp.current()

    webhook_service = app.webhook_service
    order_handler = app.shopify_webhook_order_handler
    user_handler = app.shopify_webhook_user_handler
    cart_handler = app.shopify_webhook_cart_handler
    checkout_handler = app.shopify_webhook_checkout_handler
    product_handler = app.shopify_webhook_product_handler
    fulfillment_handler = FlaskApp.current().shopify_webhoook_fullfillment_handler

    response_payload = {}

    try:
        topic_handlers = {
            "orders/paid": order_handler.order_paid,
            "customers/create": user_handler.customer_update,
            "customers/update": user_handler.customer_update,
            "carts/create": cart_handler.cart_create,
            "carts/update": cart_handler.cart_update,
            "checkouts/create": checkout_handler.checkout_create,
            "checkouts/update": checkout_handler.checkout_update,
            "checkouts/delete": checkout_handler.checkout_delete,
            "products/create": product_handler.product_create,
            "products/update": product_handler.product_update,
            "products/delete": product_handler.product_delete,
            "fulfillments/create": fulfillment_handler.fulfillment_create,
        }

        if topic not in topic_handlers:
            return None, 200

        webhook = webhook_service.store_webhook(topic, payload)
        response_payload = topic_handlers[topic](webhook.id, payload)
    except Exception as e:
        logger.exception(f"Error handling Shopify webhook: {e}")
    finally:
        return response_payload, 200
