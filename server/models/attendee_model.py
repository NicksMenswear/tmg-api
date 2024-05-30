from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr

from server.models.user_model import UserRequestModel


class CreateAttendeeModel(UserRequestModel):
    email: EmailStr
    event_id: UUID
    style: bool = False
    invite: bool = False
    pay: bool = False
    size: bool = False
    ship: bool = False
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
    is_active: bool = True


class AttendeeModel(BaseModel):
    id: UUID
    user_id: UUID
    event_id: UUID
    role_id: Optional[UUID]
    look_id: Optional[UUID]
    style: bool
    invite: bool
    pay: bool
    size: bool
    ship: bool
    is_active: bool

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(
            include={"id", "user_id", "event_id", "role_id", "look_id", "style", "invite", "pay", "size", "ship"}
        )


class AttendeeUserModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

    def to_response(self):
        return self.dict(
            include={
                "first_name",
                "last_name",
                "email",
            }
        )


class EnrichedAttendeeModel(AttendeeModel):
    user: AttendeeUserModel

    def to_response(self):
        attendee = super().to_response()
        user = self.user.to_response()
        attendee["user"] = user

        return attendee


class UpdateAttendeeModel(BaseModel):
    style: bool = False
    invite: bool = False
    pay: bool = False
    size: bool = False
    ship: bool = False
    is_active: bool = True
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
