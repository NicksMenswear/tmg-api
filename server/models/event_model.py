from enum import Enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class EventUserStatus(str, Enum):
    OWNER = "owner"
    ATTENDEE = "attendee"

    def __str__(self):
        return self.value


class EventTypeModel(str, Enum):
    WEDDING = "wedding"
    PROM = "prom"
    OTHER = "other"

    def __str__(self):
        return self.value


class EventRequestModel(BaseModel):
    name: str
    event_at: datetime

    @field_validator("name")
    @classmethod
    def name_length(cls, v):
        if len(v) < 2 or len(v) > 64:
            raise ValueError("Event name must be between 2 and 64 characters long")

        return v

    @field_validator("event_at")
    @classmethod
    def date_in_the_future(cls, v):
        if v <= datetime.now():
            raise ValueError("Event date must be in the future")
        return v


class CreateEventModel(EventRequestModel):
    user_id: UUID
    is_active: bool = True
    type: EventTypeModel = EventTypeModel.WEDDING


class EventModel(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    event_at: datetime
    is_active: bool
    status: EventUserStatus = EventUserStatus.OWNER
    type: EventTypeModel

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(include={"id", "user_id", "name", "event_at", "status", "type"})


class UpdateEventModel(EventRequestModel):
    pass
