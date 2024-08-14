import logging

from server.controllers.util import hmac_verification, error_handler, log_request
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
@log_request
def sync_contact(sync_contact):
    activecampaign_service = FlaskApp.current().activecampaign_service

    activecampaign_service.sync_contact(**sync_contact)

    return None, 201


@hmac_verification
@error_handler
@log_request
def track_event(track_event):
    activecampaign_service = FlaskApp.current().activecampaign_service

    activecampaign_service.track_event(**track_event)

    return None, 201
