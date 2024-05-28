from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from server.models.user_model import UserRequestModel


class CreateAttendeeModel(UserRequestModel):
    email: EmailStr
    event_id: UUID
    style: int = 0
    invite: int = 0
    pay: int = 0
    size: int = 0
    ship: int = 0
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
    is_active: bool = True


class AttendeeModel(BaseModel):
    id: UUID
    attendee_id: UUID  # user_id
    event_id: UUID
    role_id: Optional[UUID]
    look_id: Optional[UUID]
    style: int = 0
    invite: int = 0
    pay: int = 0
    size: int = 0
    ship: int = 0
    is_active: bool

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(
            include={"id", "attendee_id", "event_id", "role_id", "look_id", "style", "invite", "pay", "size", "ship"}
        )


class EnrichedAttendeeModel(AttendeeModel):
    first_name: str
    last_name: str
    email: EmailStr

    def to_response(self):
        return self.dict(
            include={
                "id",
                "attendee_id",
                "event_id",
                "role_id",
                "look_id",
                "style",
                "invite",
                "pay",
                "size",
                "ship",
                "first_name",
                "last_name",
                "email",
            }
        )


class UpdateAttendeeModel(BaseModel):
    style: int = 0
    invite: int = 0
    pay: int = 0
    size: int = 0
    ship: int = 0
    is_active: bool = True
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
