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

    webhook_service = FlaskApp.current().webhook_service

    try:
        if topic == "orders/paid":
            webhook_service.handle_orders_paid(payload)
        else:
            logger.debug(f"Unhandled Shopify webhook topic: {topic}")
    finally:
        return "OK", 200
