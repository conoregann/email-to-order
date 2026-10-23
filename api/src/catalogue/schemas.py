from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateProduct(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)
    sku: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    name: str = Field(min_length=1, max_length=300)
    pack_size: int = Field(strict=True, ge=1, le=1000000)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock_cases: int = Field(strict=True, ge=0, le=1000000)

    @field_validator("sku")
    @classmethod
    def uppercase_sku(cls, value: str) -> str:
        return value.upper()

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
