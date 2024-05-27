from enum import Enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class EventUserStatus(str, Enum):
    OWNER = "owner"
    ATTENDEE = "attendee"

    def __str__(self):
        return self.value


class EventRequestModel(BaseModel):
    event_name: str
    event_date: datetime

    @field_validator("event_name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Event name must be between 2 and 64 characters long")

        return v

    @field_validator("event_date")
    @classmethod
    def date_in_the_future(cls, v):
        if v <= datetime.now():
            raise ValueError("Event date must be in the future")
        return v


class CreateEventModel(EventRequestModel):
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

    def to_response(self):
        return self.dict(include={"id", "user_id", "event_name", "event_date", "status"})


class UpdateEventModel(EventRequestModel):
    pass
