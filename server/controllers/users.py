import logging

from flask import jsonify

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create_user(user_data):
    user_service = FlaskApp.current().user_service

    user = user_service.create_user(user_data)

    return user.to_dict(), 201


@hmac_verification
@error_handler
def get_user_by_email(email):
    user_service = FlaskApp.current().user_service

    user = user_service.get_user_by_email(email)

    if not user:
        return jsonify({"errors": "User not found"}), 404

    return user.to_dict(), 200


@hmac_verification
@error_handler
def get_user_events(user_id, status=None):
    user_service = FlaskApp.current().user_service

    events = user_service.get_user_events(user_id, status=status)

    return events, 200


@hmac_verification
@error_handler
def get_user_looks(user_id):
    user_service = FlaskApp.current().user_service

    looks = user_service.get_user_looks(user_id)

    return [look.to_dict() for look in looks]


@hmac_verification
@error_handler
def update_user(user_id, user_data):
    user_service = FlaskApp.current().user_service

    user = user_service.update_user(user_id, user_data)

    return user.to_dict(), 200
