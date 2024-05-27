import logging
import uuid

from server.controllers.util import hmac_verification, error_handler
from server.flask_app import FlaskApp
from server.models.discount_model import CreateDiscountIntentAmount, CreateDiscountIntentPayFull

logger = logging.getLogger(__name__)


@hmac_verification
@error_handler
def get_gift_discounts(event_id):
    discount_service = FlaskApp.current().discount_service

    discounts = discount_service.get_gift_discounts(uuid.UUID(event_id))

    return [discount.to_response() for discount in discounts], 200


@hmac_verification
@error_handler
def create_discount_intents(event_id, intents):
    discount_service = FlaskApp.current().discount_service

    discount_intents = []

    for intent in intents:
        if "amount" in intent:
            discount_intents.append(CreateDiscountIntentAmount(**intent))
        elif "pay_full" in intent:
            discount_intents.append(CreateDiscountIntentPayFull(**intent))
        else:
            raise ValueError("Invalid discount intent")

    discounts = discount_service.create_discount_intents(uuid.UUID(event_id), discount_intents)

    return [discount.to_response() for discount in discounts], 201
