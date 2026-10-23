from pydantic import BaseModel, ConfigDict

class SampleEmail(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    title: str
    scenario: str
    body: str
