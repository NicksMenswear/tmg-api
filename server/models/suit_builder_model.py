import os
from typing import Dict, List, Any, Optional
from uuid import UUID

from pydantic import RootModel

from server.models import CoreModel

STAGE = os.getenv("STAGE", "dev")
DATA_ENDPOINT_HOST = f"data.{STAGE if STAGE == 'prd' else 'dev'}.tmgcorp.net"
DATA_URL = f"https://{DATA_ENDPOINT_HOST}/suit-builder/v1"


class CreateSuitBuilderModel(CoreModel):
    type: str
    sku: str
    image_url: Optional[str] = None
    icon_url: Optional[str] = None
    index: int = 0


class SuitBuilderItemModel(CoreModel):
    id: UUID
    type: str
    sku: str
    name: str
    index: int
    variant_id: int
    product_id: int
    is_active: bool
    price: float
    selected: bool = False

    class Config:
        from_attributes = True

    def to_response(self) -> Dict[str, Any]:
        response = self.model_dump(include={"type", "sku", "name", "variant_id", "price", "selected"})

        response["image_url"] = f"{DATA_URL}/{self.type}/{self.sku}.png"
        response["icon_url"] = f"{DATA_URL}/{self.type}/{self.sku}-icon.png"

        return response

    def to_response_enriched(self) -> Dict[str, Any]:
        response = self.to_response()

        response["id"] = self.id
        response["index"] = self.index
        response["is_active"] = self.is_active
        response["product_id"] = self.product_id

        return response


class SuitBuilderItemsCollection(RootModel[Dict[str, Dict[str, Any]]]):
    def __init__(self, **data):
        super().__init__(root=data.get("root", {}))

    def add_item(self, item: SuitBuilderItemModel) -> None:
        if item.type not in self.root:
            self.root[item.type] = []
            # Select first by default
            # TODO change for edit look or build look from existing
            item.selected = True

        self.root[item.type].append(item)

    def to_response(self, enriched: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        return {
            key: {
                # Select section by default
                # TODO change for edit look or build look from existing
                "selected": True,
                "items": [item.to_response_enriched() if enriched else item.to_response() for item in items],
            }
            for key, items in self.root.items()
        }
