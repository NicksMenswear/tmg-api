from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, PositiveInt

from server.database.models import DiscountType


class CreateDiscountIntent(BaseModel):
    attendee_id: UUID


class CreateDiscountIntentAmount(CreateDiscountIntent):
    amount: PositiveInt


class CreateDiscountIntentPayFull(CreateDiscountIntent):
    pay_full: bool = True


class EventDiscountLookModel(BaseModel):
    id: UUID
    name: Optional[str] = None
    price: Optional[int] = 0


class EventDiscountCodeModel(BaseModel):
    code: str
    amount: int
    type: str
    used: bool


class EventDiscountModel(BaseModel):
    attendee_id: UUID
    event_id: UUID
    first_name: str
    last_name: str
    amount: int = 0
    look: EventDiscountLookModel
    codes: List[EventDiscountCodeModel] = []

    def to_response(self):
        return self.model_dump()


class DiscountModel(BaseModel):
    id: UUID
    event_id: UUID
    attendee_id: UUID
    amount: Optional[int]
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
            }
        )

        return {**response, "type": self.type.value}


class ApplyDiscountModel(BaseModel):
    event_id: UUID
    shopify_cart_id: str
