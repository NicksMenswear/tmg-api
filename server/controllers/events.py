import logging

from flask import jsonify

from server.controllers.util import hmac_verification
from server.services import NotFoundError, ServiceError, DuplicateError
from server.services.event import EventService

logger = logging.getLogger(__name__)


# @hmac_verification
# def get_event(event_id):
#     event_service = EventService()
#
#     try:
#         event = event_service.get_event(event_id)
#     except NotFoundError as e:
#         logger.debug(e)
#         return jsonify({"errors": e.message}), 404
#     except ServiceError as e:
#         logger.exception(e)
#         return jsonify({"errors": e.message}), 500
#
#     return event.to_dict(), 200


@hmac_verification
def create_event(event):
    event_service = EventService()

    try:
        event = event_service.create_event(event)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except DuplicateError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 409
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return event.to_dict(), 201


@hmac_verification
def update_event(event):
    event_service = EventService()

    try:
        event = event_service.update_event(event)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return event.to_dict(), 200


@hmac_verification
def soft_delete_event(event):
    event_service = EventService()

    try:
        event_service.soft_delete_event(event)
    except NotFoundError as e:
        logger.debug(e)
        return jsonify({"errors": e.message}), 404
    except ServiceError as e:
        logger.exception(e)
        return jsonify({"errors": e.message}), 500

    return None, 204
