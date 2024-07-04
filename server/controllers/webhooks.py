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

    response_payload = {}

    try:
        topic_handlers = {
            "orders/paid": webhook_service.handle_orders_paid,
            "customers/create": webhook_service.handle_customer_update,
            "customers/update": webhook_service.handle_customer_update,
            "customers/enable": webhook_service.handle_customer_update,
            "customers/disable": webhook_service.handle_customer_update,
        }

        if topic in topic_handlers:
            response_payload = topic_handlers[topic](payload)
        else:
            logger.debug(f"Unhandled Shopify webhook topic: {topic}")
    except Exception as e:
        logger.exception(f"Error handling Shopify webhook: {e}")
    finally:
        return response_payload, 200
