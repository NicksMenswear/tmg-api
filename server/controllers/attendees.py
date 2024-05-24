import logging
import uuid

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.attendee_model import CreateAttendeeModel, UpdateAttendeeModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.get_attendee_by_id(uuid.UUID(attendee_id))

    return attendee.to_response(), 200


@hmac_verification
@error_handler
def create_attendee(attendee_data):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.create_attendee(CreateAttendeeModel(**attendee_data))

    return attendee.to_response(), 201


@hmac_verification
@error_handler
def update_attendee(attendee_id, attendee_data):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.update_attendee(uuid.UUID(attendee_id), UpdateAttendeeModel(**attendee_data))

    return attendee.to_response(), 200


@hmac_verification
@error_handler
def soft_delete_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee_service.soft_delete_attendee(uuid.UUID(attendee_id))

    return jsonify({}), 204


@hmac_verification
@error_handler
# TODO: pydantify
def apply_discounts(attendee_id, apply_discounts_request):
    discount_service = FlaskApp.current().discount_service

    event_id = apply_discounts_request["event_id"]
    shopify_cart_id = apply_discounts_request["shopify_cart_id"]

    response = discount_service.apply_discounts(attendee_id, event_id, shopify_cart_id)

    logger.info(f"Discount codes applied to cart: {response}")

    return response, 200
