from datetime import datetime
from enum import Enum
from typing import Optional, List, Any, Dict
from uuid import UUID

from pydantic import field_validator

from server.models import CoreModel
from server.models.attendee_model import AttendeeModel
from server.models.look_model import LookModel
from server.models.role_model import RoleModel
from server.models.user_model import UserModel


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


class EventRequestModel(CoreModel):
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
        v = v.replace(tzinfo=None)
        if v <= datetime.now():
            raise ValueError("Event date must be in the future")
        return v


class CreateEventModel(EventRequestModel):
    user_id: UUID
    is_active: bool = True
    type: EventTypeModel = EventTypeModel.WEDDING


class EventModel(CoreModel):
    id: UUID
    user_id: UUID
    name: str
    event_at: datetime
    is_active: bool
    status: EventUserStatus = EventUserStatus.OWNER
    type: EventTypeModel
    owner: Optional[UserModel] = None
    attendees: Optional[List[AttendeeModel]] = []
    looks: Optional[List[LookModel]] = []
    roles: Optional[List[RoleModel]] = []
    meta: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    notifications: Optional[List[Dict[str, str]]] = []

    class Config:
        from_attributes = True

    def __eq__(self, other):
        if isinstance(other, EventModel):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)

    def to_response(self):
        response = self.model_dump(include={"id", "name", "event_at", "status", "type"})

        if self.owner:
            response["owner"] = self.owner.to_response()

        return response

    def to_enriched_response(self):
        response = self.model_dump(include={"id", "name", "event_at", "status", "type", "notifications"})

        if self.owner:
            response["owner"] = self.owner.to_response()

        response["attendees"] = [attendee.to_response() for attendee in self.attendees]
        response["looks"] = [look.to_response() for look in self.looks]
        response["roles"] = [role.to_response() for role in self.roles]

        return response


class UpdateEventModel(EventRequestModel):
    pass
