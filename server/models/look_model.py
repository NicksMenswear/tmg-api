from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class LookRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Look name must be between 2 and 64 characters long")

        return v


class CreateLookModel(LookRequest):
    user_id: UUID
    product_specs: dict
    is_active: bool = True
    image: Optional[str] = None


class LookModel(BaseModel):
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
        return self.dict(include={"id", "name", "product_specs", "image_path"})

    def to_response_with_price(self):
        return self.dict(include={"id", "name", "product_specs", "image_path", "price"})


class UpdateLookModel(LookRequest):
    product_specs: dict
