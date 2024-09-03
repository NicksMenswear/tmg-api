from typing import List

from pydantic import BaseModel

GROUND_SHIPPING_NAME: str = "Ground"
GROUND_SHIPPING_PRICE_IN_CENTS: str = "0"
EXPEDITED_SHIPPING_NAME: str = "Expedited"
EXPEDITED_SHIPPING_PRICE_IN_CENTS: str = "4500"


class ShippingRateModel(BaseModel):
    service_name: str = GROUND_SHIPPING_NAME
    service_code: str = "TMG"
    total_price: str = GROUND_SHIPPING_PRICE_IN_CENTS
    currency: str = "USD"

    def to_response(self):
        return {
            "service_name": self.service_name,
            "service_code": self.service_code,
            "total_price": self.total_price,
            "currency": self.currency,
        }


class GroundShippingRateModel(ShippingRateModel):
    service_name: str = GROUND_SHIPPING_NAME
    total_price: str = GROUND_SHIPPING_PRICE_IN_CENTS


class ExpeditedShippingRateModel(ShippingRateModel):
    service_name: str = EXPEDITED_SHIPPING_NAME
    total_price: str = EXPEDITED_SHIPPING_PRICE_IN_CENTS


class ShippingPriceModel(BaseModel):
    rates: List[ShippingRateModel]

    def to_response(self):
        return {"rates": [rate.to_response() for rate in self.rates]}
