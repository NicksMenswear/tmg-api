from typing import Optional

from pydantic import BaseModel


class ShipHeroProductModel(BaseModel):
    id: str
    name: str
    sku: str
    price: Optional[float] = 0.0
