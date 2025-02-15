from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import field_validator

from server.models import CoreModel


class LookRequest(CoreModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Look name must be between 2 and 64 characters long")

        return v


class ProductSpecType(str, Enum):
    VARIANT = "variant"
    SKU = "sku"


class CreateLookModel(LookRequest):
    user_id: UUID
    spec_type: ProductSpecType = ProductSpecType.VARIANT
    product_specs: dict
    is_active: bool = True
    image: Optional[str] = None


class LookModel(CoreModel):
    id: UUID
    name: str
    user_id: UUID
    product_specs: dict
    image_path: Optional[str]
    is_active: bool
    price: float = 0.0

    class Config:
        from_attributes = True

    def to_response(self):
        return self.model_dump(include={"id", "name", "product_specs", "image_path"})

    def to_response_with_price(self):
        return self.model_dump(include={"id", "name", "product_specs", "image_path", "price"})


class UpdateLookModel(LookRequest):
    product_specs: dict
