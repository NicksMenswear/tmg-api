from flask import current_app as app
from flask import jsonify

from server.controllers.hmac_1 import hmac_verification
from server.database.database_manager import get_database_session, session_factory
from server.services import NotFoundError, ServiceError
from server.services.order import OrderService

db = get_database_session()


@hmac_verification()
def create_order(order):
    order_service = OrderService(session_factory())

    try:
        order = order_service.create_order(**order)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return order, 201


@hmac_verification()
def get_order_by_id(order_id):
    order_service = OrderService(session_factory())

    order = order_service.get_order_by_id(order_id)

    if not order:
        return jsonify({"errors": NotFoundError.MESSAGE}), 404

    return order, 200


@hmac_verification()
def get_orders(user_id=None, event_id=None):
    order_service = OrderService(session_factory())

    order = order_service.get_orders_by_user_and_event(user_id, event_id)

    return order, 200


@hmac_verification()
def update_order(order):
    order_service = OrderService(session_factory())

    try:
        order = order_service.update_order(**order)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return order, 200


@hmac_verification()
def delete_order(order_id):
    order_service = OrderService(session_factory())

    try:
        order_service.delete_order(order_id)
    except NotFoundError as e:
        app.logger.debug(e.message, e)
        return jsonify({"errors": NotFoundError.MESSAGE}), 404
    except ServiceError as e:
        app.logger.error(e.message, e)
        return jsonify({"errors": e.message}), 500

    return None, 204
