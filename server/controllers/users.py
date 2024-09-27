import logging
import uuid

from pydantic import validate_email

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.event_model import EventUserStatus
from server.models.user_model import CreateUserModel, UpdateUserModel
from server.services.user_service import UserService

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create_user(create_user):
    user_service = FlaskApp.current().user_service

    user = user_service.create_user(CreateUserModel(**create_user), True)

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
def get_user_events(user_id, status=None, enriched=False):
    event_service = FlaskApp.current().event_service

    events = event_service.get_user_events(
        uuid.UUID(user_id), status=EventUserStatus(status) if status else None, enriched=enriched
    )

    if enriched:
        event_models = [event.to_enriched_response() for event in events]
    else:
        event_models = [event.to_response() for event in events]

    return event_models


@hmac_verification
@error_handler
def get_user_looks(user_id):
    look_service = FlaskApp.current().look_service

    looks = look_service.get_looks_by_user_id(uuid.UUID(user_id))

    return [look.to_response_with_price() for look in looks], 200


@hmac_verification
@error_handler
def update_user(user_id, update_user):
    user_service = FlaskApp.current().user_service

    user = user_service.update_user(uuid.UUID(user_id), UpdateUserModel(**update_user))

    return user.to_response(), 200


@hmac_verification
@error_handler
def generate_activation_url(user_id):
    user_service: UserService = FlaskApp.current().user_service

    return {"activation_url": user_service.generate_activation_url(user_id)}
