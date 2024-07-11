from typing import Optional

from pydantic import BaseModel


class ShopifyVariantModel(BaseModel):
    product_id: str
    product_title: str
    variant_id: str
    variant_title: str
    variant_price: Optional[float] = None
    variant_sku: str
