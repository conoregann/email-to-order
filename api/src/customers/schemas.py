from pydantic import BaseModel, ConfigDict, Field


class CreateCustomer(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

class Address(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    label: str
    lines: tuple[str, ...]

class Customer(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    name: str
    email: str
    addresses: tuple[Address, ...]
