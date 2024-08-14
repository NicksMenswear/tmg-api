import logging
import uuid

from flask import request

from server.controllers import FORCE_DELETE_HEADER
from server.controllers.util import hmac_verification, error_handler, log_request
from server.flask_app import FlaskApp
from server.models.attendee_model import CreateAttendeeModel, UpdateAttendeeModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
@log_request
def get_attendee_by_id(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.get_attendee_by_id(uuid.UUID(attendee_id))

    return attendee.to_response(), 200


@hmac_verification
@error_handler
@log_request
def create_attendee(create_attendee):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.create_attendee(CreateAttendeeModel(**create_attendee))

    return attendee.to_response(), 201


@hmac_verification
@error_handler
@log_request
def update_attendee(attendee_id, update_attendee):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.update_attendee(uuid.UUID(attendee_id), UpdateAttendeeModel(**update_attendee))

    return attendee.to_response(), 200


@hmac_verification
@error_handler
@log_request
def delete_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    force = request.headers.get(FORCE_DELETE_HEADER, "false").lower() == "true"
    attendee_service.delete_attendee(uuid.UUID(attendee_id), force)

    return None, 204


@hmac_verification
@error_handler
@log_request
def send_invites(attendee_ids):
    attendee_service = FlaskApp.current().attendee_service

    attendee_uuids = [uuid.UUID(attendee_id) for attendee_id in attendee_ids]
    attendee_service.send_invites(attendee_uuids)

    return None, 201


@hmac_verification
@error_handler
@log_request
def apply_discounts(attendee_id, apply_discounts_request):
    discount_service = FlaskApp.current().discount_service

    shopify_cart_id = apply_discounts_request.get("shopify_cart_id")
    event_id = apply_discounts_request.get("event_id")
    event_id = uuid.UUID(event_id) if event_id else None
    bundle_variant_id = apply_discounts_request.get("bundle_variant_id")

    response = discount_service.apply_discounts(attendee_id, shopify_cart_id, event_id, bundle_variant_id)

    logger.info(f"Discount codes applied to cart: {response}")

    return response, 200
