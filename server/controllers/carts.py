from flask import jsonify

from server.controllers.shopify import *
from server.controllers.util import hmac_verification
from server.services import ServiceError, NotFoundError
from server.services.cart import CartService

logger = logging.getLogger(__name__)


shopify_store = os.getenv("shopify_store")
admin_api_access_token = os.getenv("admin_api_access_token")


@hmac_verification
def create_cart(cart):
    cart_service = CartService()

    try:
        cart = cart_service.create_cart(cart)
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return str(cart.id), 201


@hmac_verification
def get_cart_by_id(cart_id):
    cart_service = CartService()

    try:
        cart = cart_service.get_cart_by_id(cart_id)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404

    return cart, 200


@hmac_verification
def get_cart_by_event_attendee(event_id, attendee_id):
    cart_service = CartService()

    try:
        return cart_service.get_cart_by_event_attendee(event_id, attendee_id), 200
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500


@hmac_verification
def update_cart(cart):
    cart_service = CartService()

    try:
        cart = cart_service.update_cart(cart)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return cart.to_dict(), 200
