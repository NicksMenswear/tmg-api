from typing import List, Any
from uuid import UUID

from server.database.models import Size
from server.models import CoreModel


class CreateSizeRequestModel(CoreModel):
    user_id: UUID
    data: List[Any]


class SizeModel(CoreModel):
    id: UUID
    user_id: UUID
    data: List[Any]
    jacket_length: str
    jacket_size: str
    vest_size: str
    pant_size: str
    shirt_sleeve_length: str
    shirt_neck_size: str

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

        return cls(id=size.id, user_id=size.user_id, data=size.data, **sizing_map)
