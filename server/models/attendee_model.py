from typing import Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateAttendeeModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    event_id: UUID
    style: int = 0
    invite: int = 0
    pay: int = 0
    size: int = 0
    ship: int = 0
    role: Union[None, UUID]
    look_id: Union[None, UUID]
    is_active: bool = True


class AttendeeModel(BaseModel):
    id: UUID
    attendee_id: UUID  # user_id
    event_id: UUID
    role: Union[None, UUID]
    look_id: Union[None, UUID]
    style: int = 0
    invite: int = 0
    pay: int = 0
    size: int = 0
    ship: int = 0
    is_active: bool = True

    class Config:
        from_attributes = True
        orm_mode = True

    def to_response(self):
        return self.dict(
            include={"id", "attendee_id", "event_id", "role", "look_id", "style", "invite", "pay", "size", "ship"}
        )


class UpdateAttendeeModel(BaseModel):
    role: Union[None, UUID]
    look_id: Union[None, UUID]
    style: int = 0
    invite: int = 0
    pay: int = 0
    size: int = 0
    ship: int = 0
    is_active: bool = True
