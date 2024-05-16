import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import DuplicateError, ServiceError, NotFoundError
from server.services.attendee import AttendeeService
from server.services.discount import DiscountService
from server.services.event import EventService
from server.services.shopify import ShopifyService
from server.services.user import UserService

logger = logging.getLogger(__name__)


@hmac_verification
def get_attendee(attendee_id):
    attendee_service = AttendeeService()

    attendee = attendee_service.get_attendee_by_id(attendee_id)

    if not attendee:
        return jsonify({"errors": "Attendee not found"}), 404

    try:
        attendee = attendee_service.get_attendee_by_id(attendee_id)
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to get attendee"}), 500

    return attendee.to_dict(), 200


@hmac_verification
def create_attendee(attendee_data):
    attendee_service = AttendeeService()

    try:
        attendee = attendee_service.create_attendee(attendee_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": DuplicateError.MESSAGE}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to create attendee"}), 500

    return attendee.to_dict(), 201


@hmac_verification
def update_attendee(attendee_id, attendee_data):
    attendee_service = AttendeeService()

    try:
        attendee = attendee_service.update_attendee(attendee_id, attendee_data)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return attendee.to_dict(), 200


@hmac_verification
def soft_delete_attendee(attendee_id):
    attendee_service = AttendeeService()

    try:
        attendee_service.soft_delete_attendee(attendee_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return None, 204


@hmac_verification
def apply_discounts(attendee_id, apply_discounts_request):
    user_service = UserService()
    event_service = EventService()
    discount_service = DiscountService()

    event_id = apply_discounts_request["event_id"]
    shopify_cart_id = apply_discounts_request["shopify_cart_id"]

    discounts = user_service.get_grooms_gift_paid_but_not_used_discounts(attendee_id)

    num_attendees = event_service.get_num_attendees_for_event(event_id)

    if num_attendees >= 4:
        existing_discount = discount_service.get_group_discount_for_attendee(attendee_id)

        if not existing_discount:
            discount = discount_service.create_group_discount_for_attendee(attendee_id, event_id)
            discounts.append(discount)
        else:
            discounts.append(existing_discount)

    discounts = [discount for discount in discounts]

    if not discounts:
        return "{}", 200

    shopify_service = ShopifyService()
    response = shopify_service.apply_discount_codes_to_cart(shopify_cart_id, [discount.code for discount in discounts])

    logger.info(f"Discount codes applied to cart: {apply_discounts_request}")
    logger.info(f"Response body: {response}")

    return "{}", 200
