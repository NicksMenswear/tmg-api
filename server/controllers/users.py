import logging
import uuid

from pydantic import validate_email

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.event_model import EventUserStatus
from server.models.user_model import CreateUserModel, UpdateUserModel

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create_user(user_data):
    user_service = FlaskApp.current().user_service

    user = user_service.create_user(CreateUserModel(**user_data))

    return user.to_response(), 201


@hmac_verification
@error_handler
def get_user_by_email(email):
    user_service = FlaskApp.current().user_service

    validate_email(email)

    user = user_service.get_user_by_email(email)

    return user.to_response(), 200


@hmac_verification
@error_handler
def get_user_events(user_id, status=None):
    event_service = FlaskApp.current().event_service

    events = event_service.get_user_events(user_id, status=EventUserStatus(status) if status else None)

    return [event.to_response() for event in events], 200


@hmac_verification
@error_handler
def get_user_looks(user_id):
    look_service = FlaskApp.current().look_service

    return look_service.get_looks_by_user_id(user_id)


@hmac_verification
@error_handler
def update_user(user_id, user_data):
    user_service = FlaskApp.current().user_service

    user = user_service.update_user(uuid.UUID(user_id), UpdateUserModel(**user_data))

    return user.to_response(), 200
