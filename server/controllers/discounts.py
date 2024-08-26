import logging
import uuid

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.discount_model import CreateDiscountIntent

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_owner_discounts_for_event(event_id):
    discount_service = FlaskApp.current().discount_service

    discounts = discount_service.get_owner_discounts_for_event(uuid.UUID(event_id))

    return [discount.to_response() for discount in discounts], 200


@hmac_verification
@error_handler
def create_discount_intents(event_id, intents):
    discount_service = FlaskApp.current().discount_service

    discount_intents = [CreateDiscountIntent(**intent) for intent in intents]

    return discount_service.create_discount_intents(uuid.UUID(event_id), discount_intents).to_response(), 201
