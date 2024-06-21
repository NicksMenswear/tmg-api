from uuid import UUID

from pydantic import field_validator

from server.models import CoreModel


class RoleRequestModel(CoreModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Role name must be between 2 and 64 characters long")

        return v


class CreateRoleModel(RoleRequestModel):
    event_id: UUID
    is_active: bool = True


class RoleModel(CoreModel):
    id: UUID
    event_id: UUID
    name: str
    is_active: bool

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(include={"id", "name", "event_id"})


class UpdateRoleModel(RoleRequestModel):
    pass
