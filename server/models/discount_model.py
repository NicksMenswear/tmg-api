from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import PositiveFloat

from server.database.models import DiscountType
from server.models import CoreModel


class CreateDiscountIntent(CoreModel):
    attendee_id: UUID
    amount: PositiveFloat


class DiscountGiftCodeModel(CoreModel):
    code: str
    amount: float
    type: str
    used: bool

    def to_response(self):
        return self.dict()


class DiscountModel(CoreModel):
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


class ApplyDiscountModel(CoreModel):
    event_id: UUID
    shopify_cart_id: str


class DiscountLookModel(CoreModel):
    id: UUID
    name: str
    price: float

    def to_response(self):
        return self.model_dump()


class DiscountStatusModel(CoreModel):
    style: bool
    invite: bool
    pay: bool

    def to_response(self):
        return self.model_dump()


class EventDiscountModel(CoreModel):
    event_id: UUID
    amount: float = 0.0
    remaining_amount: float = 0.0
    type: DiscountType
    attendee_id: UUID
    user_id: UUID
    first_name: str
    last_name: str
    status: DiscountStatusModel
    look: Optional[DiscountLookModel] = None
    gift_codes: List[DiscountGiftCodeModel] = []

    def to_response(self):
        response = self.dict(
            include={"event_id", "amount", "remaining_amount", "attendee_id", "user_id", "first_name", "last_name"}
        )
        response["type"] = self.type.value
        response["status"] = self.status.to_response()
        response["look"] = self.look.to_response() if self.look else None
        response["gift_codes"] = [gift_code.to_response() for gift_code in self.gift_codes]

        return response


class DiscountPayResponseModel(CoreModel):
    variant_id: int

    def to_response(self):
        return self.model_dump()
