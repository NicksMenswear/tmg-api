import os
from typing import Any
from uuid import UUID

from pydantic import RootModel

from server.models import CoreModel

STAGE = os.getenv("STAGE", "dev")
DATA_ENDPOINT_HOST = f"data.{STAGE if STAGE == 'prd' else 'dev'}.tmgcorp.net"
DATA_URL = f"https://{DATA_ENDPOINT_HOST}/suit-builder/v1"


class CreateSuitBuilderModel(CoreModel):
    type: str
    sku: str
    image_url: str | None = None
    icon_url: str | None = None
    index: int = 0


class SuitBuilderItemModel(CoreModel):
    id: UUID
    type: str
    sku: str
    variant_id: int
    name: str
    index: int
    is_active: bool
    price: float
    compare_at_price: float | None = None

    class Config:
        from_attributes = True

    def to_response(self) -> dict[str, Any]:
        response = self.model_dump(include={"type", "sku", "variant_id", "name", "price", "compare_at_price"})

        response["image_url"] = f"{DATA_URL}/{self.type}/{self.sku}.png"
        response["icon_url"] = f"{DATA_URL}/{self.type}/{self.sku}-icon.png"

        return response

    def to_response_enriched(self) -> dict[str, Any]:
        response = self.to_response()

        response["id"] = self.id
        response["index"] = self.index
        response["is_active"] = self.is_active

        return response


class SuitBuilderItemsCollection(RootModel[dict[str, list[SuitBuilderItemModel]]]):
    def __init__(self, **data):
        super().__init__(root=data.get("root", {}))

    def add_item(self, item: SuitBuilderItemModel) -> None:
        if item.type not in self.root:
            self.root[item.type] = []

        self.root[item.type].append(item)

    def to_response(self, enriched: bool = False) -> dict[str, list[dict[str, Any]]]:
        return {
            key: [item.to_response_enriched() if enriched else item.to_response() for item in items]
            for key, items in self.root.items()
        }
