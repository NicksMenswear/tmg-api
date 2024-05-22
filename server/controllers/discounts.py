import logging

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_groom_gift_discounts(event_id):
    discount_service = FlaskApp.current().discount_service

    groom_gift_discounts = discount_service.get_groom_gift_discounts(event_id)

    return groom_gift_discounts, 200


@hmac_verification
@error_handler
def create_discount_intents(event_id, intents):
    discount_service = FlaskApp.current().discount_service

    discounts = discount_service.create_discount_intents(event_id, intents)

    return [discount.to_dict() for discount in discounts], 201
