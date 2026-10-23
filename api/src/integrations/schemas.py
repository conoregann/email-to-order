"""Provider facts only: no catalogue authority or approval decisions."""
from datetime import date
from decimal import Decimal
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class FactModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ExtractedLine(FactModel):
    description: str = Field(max_length=300)
    explicit_sku: str | None = Field(max_length=80)
    quantity: Decimal | None = Field(max_digits=10, decimal_places=3)
    unit: Literal["case", "unit", "unknown"]


class Extraction(FactModel):
    customer_name: str = Field(max_length=200)
    customer_email: str = Field(max_length=320)
    delivery_address: str = Field(max_length=1500)
    delivery_instructions: str = Field(max_length=1500)
    requested_date_text: str = Field(max_length=300)
    requested_delivery_date: date | None
    lines: list[ExtractedLine] = Field(max_length=50)

    @model_validator(mode="after")
    def absolute_date_only(self):
        if self.requested_delivery_date and (not self.requested_date_text.strip() or re.search(
            r"\b(today|tomorrow|yesterday|next|this|in \d+ days?)\b", self.requested_date_text, re.I
        )):
            raise ValueError("Relative dates have no trusted source timestamp")
        return self
