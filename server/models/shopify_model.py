from typing import Optional, List

from pydantic import BaseModel


class ShopifyCustomer(BaseModel):
    gid: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    state: str = "enabled"
    tags: List[str] = []

    def get_id(self) -> int:
        return int(self.gid.removeprefix("gid://shopify/Customer/"))


class ShopifyVariantModel(BaseModel):
    product_id: str
    product_title: str
    variant_id: str
    variant_title: str
    variant_price: Optional[float] = None
    variant_sku: str
    image_url: Optional[str] = None
