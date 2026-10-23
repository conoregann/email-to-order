from pydantic import BaseModel, ConfigDict

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
