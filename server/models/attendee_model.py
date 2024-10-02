from typing import Optional, List
from uuid import UUID

from pydantic import EmailStr

from server.models import CoreModel
from server.models.discount_model import DiscountGiftCodeModel
from server.models.look_model import LookModel
from server.models.role_model import RoleModel


class CreateAttendeeModel(CoreModel):
    first_name: str
    last_name: str
    event_id: UUID
    email: Optional[EmailStr] = None
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
    style: bool = False
    invite: bool = False
    pay: bool = False
    size: bool = False
    ship: bool = False
    is_active: bool = True


class AttendeeModel(CoreModel):
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr] = None
    user_id: Optional[UUID] = None
    is_owner: bool = False
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
        return self.model_dump(exclude={"is_active"})


class AttendeeUserModel(CoreModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None

    def to_response(self):
        return self.model_dump()


class TrackingModel(CoreModel):
    tracking_number: str
    tracking_url: Optional[str]

    def to_response(self):
        return self.model_dump()


class EnrichedAttendeeModel(AttendeeModel):
    user: AttendeeUserModel
    role: Optional[RoleModel] = None
    look: Optional[LookModel] = None
    gift_codes: Optional[List[DiscountGiftCodeModel]] = []
    has_gift_codes: bool = False
    tracking: Optional[List[TrackingModel]] = []
    can_be_deleted: bool = False

    def to_response(self):
        attendee = super().to_response()
        user = self.user.to_response()

        attendee["user"] = user
        attendee["role"] = self.role.to_response() if self.role else None
        attendee["look"] = self.look.to_response() if self.look else None
        attendee["gift_codes"] = [gift_code.to_response() for gift_code in self.gift_codes]
        attendee["has_gift_codes"] = self.has_gift_codes
        attendee["tracking"] = [tracking.to_response() for tracking in self.tracking]
        attendee["can_be_deleted"] = self.can_be_deleted

        return attendee


class UpdateAttendeeModel(CoreModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: bool = True
    role_id: Optional[UUID] = None
    look_id: Optional[UUID] = None
