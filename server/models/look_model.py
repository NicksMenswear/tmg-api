from uuid import UUID

from pydantic import BaseModel


class CreateLookModel(BaseModel):
    look_name: str
    user_id: UUID
    product_specs: dict


class LookModel(BaseModel):
    id: UUID
    look_name: str
    user_id: UUID
    product_specs: dict

    class Config:
        from_attributes = True
        orm_mode = True

    def to_response(self):
        return self.dict(include={"id", "look_name"})


class UpdateLookModel(BaseModel):
    look_name: str
    product_specs: dict
