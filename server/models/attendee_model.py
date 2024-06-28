from typing import Optional, List
from uuid import UUID

from pydantic import EmailStr

from server.models import CoreModel
from server.models.discount_model import DiscountGiftCodeModel
from server.models.look_model import LookModel
from server.models.role_model import RoleModel
from server.models.user_model import UserRequestModel


class CreateAttendeeModel(UserRequestModel):
    email: EmailStr
    event_id: UUID
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
    is_active: bool = True


class AttendeeModel(CoreModel):
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
        return self.model_dump(
            include={"id", "user_id", "event_id", "role_id", "look_id", "style", "invite", "pay", "size", "ship"}
        )


class AttendeeUserModel(CoreModel):
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
    role: Optional[RoleModel] = None
    look: Optional[LookModel] = None
    gift_codes: Optional[List[DiscountGiftCodeModel]] = {}

    def to_response(self):
        attendee = super().to_response()
        user = self.user.to_response()
        attendee["user"] = user
        attendee["role"] = self.role.to_response() if self.role else None
        attendee["look"] = self.look.to_response() if self.look else None
        attendee["gift_codes"] = [gift_code.to_response() for gift_code in self.gift_codes]

        return attendee


class UpdateAttendeeModel(CoreModel):
    is_active: bool = True
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
