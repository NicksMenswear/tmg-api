from typing import Dict, List, Any
from uuid import UUID

from pydantic import RootModel

from server.models import CoreModel


class CreateSuitBuilderModel(CoreModel):
    type: str
    sku: str


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

    class Config:
        from_attributes = True

    def to_response(self) -> Dict[str, Any]:
        return self.model_dump(include={"type", "sku", "name", "index", "variant_id", "price"})

    def to_response_enriched(self) -> Dict[str, Any]:
        return self.model_dump(
            include={"id", "type", "sku", "name", "index", "variant_id", "product_id", "is_active", "price"}
        )


class SuitBuilderItemsCollection(RootModel[Dict[str, List[SuitBuilderItemModel]]]):
    def __init__(self, **data):
        super().__init__(root=data.get("root", {}))

    def add_item(self, item: SuitBuilderItemModel) -> None:
        if item.type not in self.root:
            self.root[item.type] = []

        self.root[item.type].append(item)

    def to_response(self, enriched: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        return {
            key: [item.to_response_enriched() if enriched else item.to_response() for item in items]
            for key, items in self.root.items()
        }
