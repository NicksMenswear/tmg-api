import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.flask_app import FlaskApp
from server.services import DuplicateError, ServiceError, NotFoundError

logger = logging.getLogger(__name__)


@hmac_verification
def get_attendee(attendee_id):
    attendee_service = FlaskApp.current().attendee_service

    try:
        attendee = attendee_service.get_attendee_by_id(attendee_id)

        if not attendee:
            return jsonify({"errors": "Attendee not found"}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": "Failed to get attendee"}), 500

    return attendee.to_dict(), 200


@hmac_verification
def create_attendee(attendee_data):
    attendee_service = FlaskApp.current().attendee_service

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
    attendee_service = FlaskApp.current().attendee_service

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
    attendee_service = FlaskApp.current().attendee_service

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
    attendee_service = FlaskApp.current().attendee_service

    event_id = apply_discounts_request["event_id"]
    shopify_cart_id = apply_discounts_request["shopify_cart_id"]

    response = attendee_service.apply_discounts(attendee_id, event_id, shopify_cart_id)

    logger.info(f"Discount codes applied to cart: {response}")

    return "{}", 200
