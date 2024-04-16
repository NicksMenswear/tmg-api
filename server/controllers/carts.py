from flask import current_app as app, jsonify

from server.controllers.hmac_1 import hmac_verification
from server.controllers.shopify import *
from server.database.database_manager import session_factory
from server.services import ServiceError, NotFoundError
from server.services.cart import CartService

shopify_store = os.getenv("shopify_store")
admin_api_access_token = os.getenv("admin_api_access_token")

db = get_database_session()


@hmac_verification()
def create_cart(cart):
    cart_service = CartService(session_factory())

    try:
        cart = cart_service.create_cart(**cart)
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return str(cart.id), 201


@hmac_verification()
def get_cart_by_id(cart_id):
    cart_service = CartService(session_factory())

    try:
        cart = cart_service.get_cart_by_id(cart_id)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404

    return cart, 200


@hmac_verification()
def get_cart_by_event_attendee(event_id, attendee_id):
    cart_service = CartService(session_factory())

    try:
        return cart_service.get_cart_by_event_attendee(event_id, attendee_id), 200
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500


@hmac_verification()
def update_cart(cart):
    cart_service = CartService(session_factory())

    try:
        cart = cart_service.update_cart(**cart)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return cart.to_dict(), 200
