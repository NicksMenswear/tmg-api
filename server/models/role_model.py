from uuid import UUID

from pydantic import BaseModel, field_validator


class RoleRequestModel(BaseModel):
    role_name: str

    @field_validator("role_name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Role name must be between 2 and 64 characters long")

        return v


class CreateRoleModel(RoleRequestModel):
    event_id: UUID


class RoleModel(BaseModel):
    id: UUID
    role_name: str
    event_id: UUID

    class Config:
        from_attributes = True
        orm_mode = True

    def to_response(self):
        return self.dict(include={"id", "role_name", "event_id"})


class UpdateRoleModel(RoleRequestModel):
    pass
