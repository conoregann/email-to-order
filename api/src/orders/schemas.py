from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class SampleEmail(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    title: str
    scenario: str
    body: str

class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class QuantityResolution(InputModel):
    requested_quantity: Decimal | None = Field(default=None, max_digits=10, decimal_places=3)
    requested_unit: Literal["case", "unit", "unknown"]
    status: Literal["unresolved", "needs_clarification", "adjusted"]
    reason: str = Field(default="", max_length=500)
    approved_quantity: Decimal | None = Field(default=None, max_digits=10, decimal_places=3)
    approved_unit: Literal["case", "unit", "unknown"] = "unknown"
    approved_sku: str | None = Field(default=None, max_length=80)

class LineValues(InputModel):
    requested_product: str = Field(default="", max_length=300)
    sku: str | None = Field(default=None, max_length=80)
    match_confirmed: bool = False
    quantity: Decimal | None = Field(default=None, max_digits=10, decimal_places=3)
    quantity_unit: Literal["case", "unit", "unknown"] = "unknown"
    quantity_resolution: QuantityResolution | None = None

class DraftValues(InputModel):
    customer_id: str | None = Field(default=None, max_length=80)
    delivery_address: str = Field(default="", max_length=1500)
    delivery_instructions: str = Field(default="", max_length=1500)
    delivery_confirmed: bool = False
    requested_delivery_date: date | None = None
    lines: list[LineValues] = Field(default_factory=list, max_length=50)

class CreateDraft(InputModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    email: str = Field(min_length=1, max_length=20000)
    sample_id: str | None = Field(default=None, max_length=80)

    @field_validator("email")
    @classmethod
    def nonempty_email(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Email must contain text")
        return value

class UpdateDraft(DraftValues):
    version: int = Field(ge=1)

class ConfirmDraft(InputModel):
    version: int = Field(ge=1)
