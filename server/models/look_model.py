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


class LookModel(BaseModel):
    id: UUID
    name: str
    user_id: UUID
    product_specs: dict

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(include={"id", "name"})


class UpdateLookModel(LookRequest):
    product_specs: dict
