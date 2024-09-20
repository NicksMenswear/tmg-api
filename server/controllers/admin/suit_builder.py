from typing import Dict, Any

from server.controllers.util import token_verification, error_handler
from server.flask_app import FlaskApp
from server.models.suit_builder_model import (
    CreateSuitBuilderModel,
    SuitBuilderItemModel,
    SuitBuilderItemsCollection,
)
from server.services.suit_builder_service import SuitBuilderService


@token_verification
@error_handler
def get_items(enriched: bool = False):
    suit_builder_service: SuitBuilderService = FlaskApp.current().suit_builder_service
    collection: SuitBuilderItemsCollection = suit_builder_service.get_items(enriched)

    return collection.to_response(enriched=enriched), 200


@token_verification
@error_handler
def add_item(item: Dict[str, str]):
    suit_builder_service: SuitBuilderService = FlaskApp.current().suit_builder_service
    item: SuitBuilderItemModel = suit_builder_service.add_item(CreateSuitBuilderModel(**item))

    return item.to_response_enriched(), 201


@token_verification
@error_handler
def patch_item(sku: str, item: Dict[str, Any]):
    suit_builder_service: SuitBuilderService = FlaskApp.current().suit_builder_service
    item: SuitBuilderItemModel = suit_builder_service.patch_item(sku, item.get("field"), item.get("value"))

    return item.to_response_enriched(), 200


@token_verification
@error_handler
def delete_item(sku: str):
    suit_builder_service: SuitBuilderService = FlaskApp.current().suit_builder_service
    suit_builder_service.delete_item(sku)

    return None, 204
