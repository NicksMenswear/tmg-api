from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel

from server.database.models import Product


#  legacy_id              | character varying           |           |          |                    | extended |             |              |
#  user_id                | uuid                        |           |          |                    | plain    |             |              |
#  event_id               | uuid                        |           |          |                    | plain    |             |              |
#  order_number           | character varying           |           |          |                    | extended |             |              |
#  order_origin           | sourcetype                  |           |          |                    | plain    |             |              |
#  order_date             | timestamp without time zone |           |          |                    | plain    |             |              |
#  status                 | character varying           |           |          |                    | extended |             |              |
#  shipped_date           | timestamp without time zone |           |          |                    | plain    |             |              |
#  received_date          | timestamp without time zone |           |          |                    | plain    |             |              |
#  ship_by_date           | timestamp without time zone |           |          |                    | plain    |             |              |
#  shipping_method        | character varying           |           |          |                    | extended |             |              |
#  outbound_tracking      | character varying           |           |          |                    | extended |             |              |
#  store_location         | storelocation               |           |          |                    | plain    |             |              |
#  order_type             | ordertype[]                 |           |          |                    | extended |             |              |
#  shipping_address_line1 | character varying           |           |          |                    | extended |             |              |
#  shipping_address_line2 | character varying           |           |          |                    | extended |             |              |
#  shipping_city          | character varying           |           |          |                    | extended |             |              |
#  shipping_state         | character varying           |           |          |                    | extended |             |              |
#  shipping_zip_code      | character varying           |           |          |                    | extended |             |              |
#  shipping_country       | character varying           |           |          |                    | extended |             |              |


class AddressTypeModel(str, Enum):
    SHIPPING = "shipping"
    BILLING = "billing"

    def __str__(self):
        return self.value


class AddressModel(BaseModel):
    type: AddressTypeModel = AddressTypeModel.SHIPPING
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None


class CreateProductModel(BaseModel):
    name: str
    sku: Optional[str] = None
    price: float = 0.0
    quantity: int = 0
    on_hand: int = 0
    meta: Optional[dict] = None


class CreateOrderModel(BaseModel):
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


class ProductModel(BaseModel):
    id: UUID
    name: str
    sku: Optional[str] = None
    price: float = 0.0
    on_hand: int = 0

    class Config:
        from_attributes = True

    def to_response(self):
        return self.dict(include={"id", "name", "sku"})


class OrderModel(BaseModel):
    id: UUID
    products: List[ProductModel]

    class Config:
        from_attributes = True

    def to_response(self):
        data = self.dict(include={"id"})
        data["products"] = [product.to_response() for product in self.products]

        return data
