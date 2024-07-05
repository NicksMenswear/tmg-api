import logging

from server.controllers.util import hmac_verification, error_handler
from server.models.user_model import CreateUserModel
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def create_contact(create_user):
    activecampaign_service = FlaskApp.current().activecampaign_service

    activecampaign_service.create_contact(CreateUserModel(**create_user))

    return None, 201
