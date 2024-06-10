from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, PositiveFloat

from server.database.models import DiscountType


class CreateDiscountIntent(BaseModel):
    attendee_id: UUID


class CreateDiscountIntentAmount(CreateDiscountIntent):
    amount: PositiveFloat


class CreateDiscountIntentPayFull(CreateDiscountIntent):
    pay_full: bool = True


class EventDiscountCodeModel(BaseModel):
    code: str
    amount: float
    type: str
    used: bool

    def to_response(self):
        return self.dict()


class DiscountModel(BaseModel):
    id: UUID
    event_id: UUID
    attendee_id: UUID
    amount: Optional[float]
    type: DiscountType
    used: bool = False
    shopify_discount_code: Optional[str] = None
    shopify_discount_code_id: Optional[int] = None
    shopify_virtual_product_id: Optional[int] = None
    shopify_virtual_product_variant_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    def to_response(self):
        response = self.dict(
            include={
                "id",
                "event_id",
                "attendee_id",
                "amount",
                "used",
                "shopify_discount_code",
                "shopify_virtual_product_variant_id",
            }
        )

        return {**response, "type": self.type.value}


class ApplyDiscountModel(BaseModel):
    event_id: UUID
    shopify_cart_id: str


class EventDiscountLookModel(BaseModel):
    id: UUID
    name: str
    price: float

    def to_response(self):
        return self.model_dump()


class EventDiscountAttendeeStatusModel(BaseModel):
    style: bool
    invite: bool
    pay: bool

    def to_response(self):
        return self.model_dump()


class EventDiscountAttendeeModel(BaseModel):
    id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    status: EventDiscountAttendeeStatusModel
    look: Optional[EventDiscountLookModel] = None

    def to_response(self):
        response = self.dict(include={"id", "user_id", "first_name", "last_name"})
        response["status"] = self.status.to_response()
        response["look"] = self.look.to_response() if self.look else None

        return response


class EventDiscountModel(BaseModel):
    id: Optional[UUID] = None
    event_id: UUID
    attendee: EventDiscountAttendeeModel
    amount: float = 0.0
    type: DiscountType
    codes: List[EventDiscountCodeModel] = []

    def to_response(self):
        response = self.dict(
            include={
                "event_id",
                "amount",
            }
        )

        if self.id:
            response["id"] = self.id
        response["type"] = self.type.value
        response["attendee"] = self.attendee.to_response()
        response["codes"] = [code.to_response() for code in self.codes]

        return response
