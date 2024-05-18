import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.flask_app import FlaskApp
from server.services import NotFoundError, ServiceError, BadRequestError

logger = logging.getLogger(__name__)


@hmac_verification
def get_groom_gift_discounts(event_id):
    discount_service = FlaskApp.current().discount_service

    try:
        groom_gift_discounts = discount_service.get_groom_gift_discounts(event_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return groom_gift_discounts, 200


@hmac_verification
def create_discount_intents(event_id, intents):
    discount_service = FlaskApp.current().discount_service

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
