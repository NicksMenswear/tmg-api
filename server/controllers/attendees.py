import logging

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.get_attendee_by_id(attendee_id)

    if not attendee:
        return jsonify({"errors": "Attendee not found"}), 404

    return attendee.to_dict(), 200


@hmac_verification
@error_handler
def create_attendee(attendee_data):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.create_attendee(attendee_data)

    return attendee.to_dict(), 201


@hmac_verification
@error_handler
def update_attendee(attendee_id, attendee_data):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.update_attendee(attendee_id, attendee_data)

    return attendee.to_dict(), 200


@hmac_verification
@error_handler
def soft_delete_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee_service.soft_delete_attendee(attendee_id)

    return None, 204


@hmac_verification
@error_handler
def apply_discounts(attendee_id, apply_discounts_request):
    discount_service = FlaskApp.current().discount_service

    event_id = apply_discounts_request["event_id"]
    shopify_cart_id = apply_discounts_request["shopify_cart_id"]

    response = discount_service.apply_discounts(attendee_id, event_id, shopify_cart_id)

    logger.info(f"Discount codes applied to cart: {response}")

    return response, 200
