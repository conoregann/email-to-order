from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Product(BaseModel):
    model_config = ConfigDict(frozen=True)
    sku: str
    name: str
    aliases: tuple[str, ...]
    pack_size: int = Field(gt=0)
    unit: Literal["case"] = "case"
    price: Decimal = Field(gt=0, decimal_places=2)
    currency: Literal["EUR"] = "EUR"
    stock_cases: int = Field(ge=0)
