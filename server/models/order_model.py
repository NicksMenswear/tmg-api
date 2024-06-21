from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from server.models import CoreModel


class AddressTypeModel(str, Enum):
    SHIPPING = "shipping"
    BILLING = "billing"

    def __str__(self):
        return self.value


class AddressModel(CoreModel):
    type: AddressTypeModel = AddressTypeModel.SHIPPING
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None


class CreateProductModel(CoreModel):
    name: str
    sku: Optional[str] = None
    price: float = 0.0
    quantity: int = 0
    on_hand: int = 0
    meta: Optional[dict] = None


class CreateOrderModel(CoreModel):
    legacy_id: Optional[str] = None
    user_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    order_number: Optional[str] = None
    order_origin: Optional[str] = None
    order_date: Optional[datetime] = None
    status: Optional[str] = None
    shipped_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    ship_by_date: Optional[datetime] = None
    shipping_method: Optional[str] = None
    outbound_tracking: Optional[str] = None
    store_location: Optional[str] = None
    order_type: Optional[List[str]] = None
    shipping_address: Optional[AddressModel] = None
    products: List[CreateProductModel] = []
    meta: Optional[dict] = None


class ProductModel(CoreModel):
    id: UUID
    name: str
    sku: Optional[str] = None
    price: float = 0.0
    on_hand: int = 0

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(include={"id", "name", "sku"})


class OrderModel(CoreModel):
    id: UUID
    order_number: str
    order_date: datetime
    products: List[ProductModel] = []
    discount_codes: List[str] = []
    event_id: Optional[UUID] = None

    class Config:
        from_attributes = True

    def to_response(self):
        data = self.dict(include={"id"})
        data["products"] = [product.to_response() for product in self.products]
        data["discount_codes"] = self.discount_codes

        return data
