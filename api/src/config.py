from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "Email to Order"
    database_url: str = ""
    cookie_secure: bool = False
    gemini_api_key: str = ""
    gemini_model: str = ""
    extraction_enabled: bool = False
    extraction_guest_limit: int = Field(default=5, ge=1, le=5)
    extraction_daily_limit: int = Field(default=25, ge=1, le=25)
    extraction_timeout_seconds: int = Field(default=30, ge=1, le=60)
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

settings = Settings()
