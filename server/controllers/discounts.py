import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import NotFoundError, ServiceError, BadRequestError
from server.services.discount import DiscountService

logger = logging.getLogger(__name__)


@hmac_verification
def get_discounts(event_id):
    discount_service = DiscountService()

    try:
        discounts = discount_service.get_groom_gift_discounts(event_id)
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return [discount.to_dict() for discount in discounts], 200


@hmac_verification
def create_discount_intents(event_id, intents):
    discount_service = DiscountService()

    try:
        discounts = discount_service.create_groom_gift_discount_intents(event_id, intents)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except BadRequestError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 400
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return [discount.to_dict() for discount in discounts], 201
