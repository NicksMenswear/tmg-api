from uuid import UUID

from pydantic import BaseModel, field_validator


class LookRequest(BaseModel):
    look_name: str

    @field_validator("look_name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Look name must be between 2 and 64 characters long")

        return v


class CreateLookModel(LookRequest):
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


class UpdateLookModel(LookRequest):
    product_specs: dict
