import logging

from server.controllers.util import error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@error_handler
def calculate_shipping_price(payload):
    shipping_service = FlaskApp.current().shipping_service

    return shipping_service.calculate_shipping_price(payload).to_response(), 200
