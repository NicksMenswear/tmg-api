from server.controllers.util import error_handler, hmac_verification
from server.flask_app import FlaskApp
from server.models.suit_builder_model import (
    SuitBuilderItemsCollection,
)
from server.services.suit_builder_service import SuitBuilderService


# @hmac_verification
@error_handler
def get_items():
    suit_builder_service: SuitBuilderService = FlaskApp.current().suit_builder_service
    collection: SuitBuilderItemsCollection = suit_builder_service.get_items()

    return collection.to_response(), 200
