import logging
import uuid

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.attendee_model import CreateAttendeeModel, UpdateAttendeeModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_attendee_by_id(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.get_attendee_by_id(uuid.UUID(attendee_id))

    return attendee.to_response(), 200


@hmac_verification
@error_handler
def create_attendee(create_attendee):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.create_attendee(CreateAttendeeModel(**create_attendee))

    return attendee.to_response(), 201


@hmac_verification
@error_handler
def update_attendee(attendee_id, update_attendee):
    attendee_service = FlaskApp.current().attendee_service

    attendee = attendee_service.update_attendee(uuid.UUID(attendee_id), UpdateAttendeeModel(**update_attendee))

    return attendee.to_response(), 200


@hmac_verification
@error_handler
def delete_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    attendee_service.delete_attendee(uuid.UUID(attendee_id))

    return None, 204


@hmac_verification
@error_handler
def send_invites(attendee_ids):
    attendee_service = FlaskApp.current().attendee_service

    attendee_uuids = [uuid.UUID(attendee_id) for attendee_id in attendee_ids]
    attendee_service.send_invites(attendee_uuids)

    return None, 201


@hmac_verification
@error_handler
def apply_discounts(attendee_id, apply_discounts_request):
    discount_service = FlaskApp.current().discount_service

    shopify_cart_id = apply_discounts_request["shopify_cart_id"]

    response = discount_service.apply_discounts(attendee_id, shopify_cart_id)

    logger.info(f"Discount codes applied to cart: {response}")

    return response, 200
