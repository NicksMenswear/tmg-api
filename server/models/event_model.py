from enum import Enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventUserStatus(str, Enum):
    OWNER = "owner"
    ATTENDEE = "attendee"

    def __str__(self):
        return self.value


class CreateEventModel(BaseModel):
    event_name: str
    event_date: datetime
    user_id: UUID
    is_active: bool = True


class EventModel(BaseModel):
    id: UUID
    user_id: UUID
    event_name: str
    event_date: datetime
    is_active: bool
    status: EventUserStatus = EventUserStatus.OWNER

    class Config:
        from_attributes = True
        orm_mode = True

    def to_response(self):
        return self.dict(include={"id", "user_id", "event_name", "event_date", "status"})


class UpdateEventModel(BaseModel):
    event_name: str
    event_date: datetime
