from uuid import UUID

from pydantic import BaseModel


class CreateRoleModel(BaseModel):
    role_name: str
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


class UpdateRoleModel(BaseModel):
    role_name: str
