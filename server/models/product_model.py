from typing import Optional
from uuid import UUID

from server.models import CoreModel


class CreateProductModel(CoreModel):
    name: str
    sku: str
    price: float = 0.0

    def to_response(self):
        return self.model_dump(include={"name", "sku", "price"})


class ProductModel(CoreModel):
    id: UUID
    name: str
    sku: str
    price: float = 0.0
    on_hand: int = 0

    class Config:
        from_attributes = True

    def to_response(self):
        return self.model_dump(include={"id", "name", "sku", "price"})
