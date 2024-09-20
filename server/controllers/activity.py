import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def page_view(view):
    activity_service = FlaskApp.current().activity_service

    activity_service.page_view(**view)

    return None, 201
