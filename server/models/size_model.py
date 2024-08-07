from typing import List, Any, Optional
from uuid import UUID
from datetime import datetime

from server.database.models import Size
from server.models import CoreModel


class CreateSizeRequestModel(CoreModel):
    user_id: UUID
    measurement_id: UUID
    data: List[Any]


class SizeModel(CoreModel):
    id: UUID
    user_id: UUID
    measurement_id: UUID
    data: List[Any]
    jacket_size: str
    jacket_length: str
    vest_size: str
    vest_length: str = "R"
    pant_size: str
    pant_length: str = "R"
    shirt_sleeve_length: str
    shirt_neck_size: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, size: Size) -> "SizeModel":
        attribute_map = {
            "SLEEVE LENGTH (SHIRT)": "shirt_sleeve_length",
            "JACKET LENGTH": "jacket_length",
            "SHIRT": "shirt_neck_size",
            "JACKET": "jacket_size",
            "VEST": "vest_size",
            "PANT": "pant_size",
        }

        sizing_map = {
            attribute_map[item["apparelId"]]: item["size"] for item in size.data if item["apparelId"] in attribute_map
        }

        return cls(
            id=size.id,
            user_id=size.user_id,
            measurement_id=size.measurement_id,
            data=size.data,
            created_at=size.created_at,
            updated_at=size.updated_at,
            **sizing_map
        )

    def to_response(self):
        return self.model_dump()
