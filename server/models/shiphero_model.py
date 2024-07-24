from pydantic import BaseModel


class ShipHeroProductModel(BaseModel):
    id: str
    name: str
    sku: str
    price: float = 0.0
