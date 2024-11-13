from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from server.models import CoreModel
from server.models.product_model import ProductModel


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


class CreateOrderModel(CoreModel):
    legacy_id: Optional[str] = None
    user_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    order_number: Optional[str] = None
    shopify_order_id: Optional[str] = None
    shopify_order_number: Optional[str] = None
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
    meta: Optional[dict] = None


class CreateOrderItemModel(CoreModel):
    order_id: UUID
    product_id: Optional[UUID] = None
    shopify_sku: Optional[str] = None
    purchased_price: float = 0.0
    quantity: int = 1


class OrderItemModel(CoreModel):
    id: UUID
    order_id: UUID
    product_id: Optional[UUID] = None
    shopify_sku: Optional[str]
    purchased_price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderModel(CoreModel):
    id: UUID
    legacy_id: Optional[str] = None
    user_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    order_number: str
    shopify_order_id: str
    shopify_order_number: str
    order_origin: Optional[str] = None
    order_date: datetime
    status: Optional[str] = None
    shipped_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    ship_by_date: Optional[datetime] = None
    shipping_method: Optional[str] = None
    shipping_address_line1: Optional[str] = None
    shipping_address_line2: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    shipping_country: Optional[str] = None
    outbound_tracking: Optional[str] = None
    store_location: Optional[str] = None
    order_type: Optional[List[str]] = None
    products: List[ProductModel] = []
    discount_codes: List[str] = []
    order_items: List[OrderItemModel] = []
    meta: Optional[dict] = None

    class Config:
        from_attributes = True

    def to_response(self):
        data = self.model_dump()
        data["discount_codes"] = self.discount_codes

        return data
