from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "Email to Order"
    database_url: str = ""
    database_url_unpooled: str = ""
    cookie_secure: bool = False
    gemini_api_key: str = ""
    gemini_model: str = ""
    extraction_enabled: bool = False
    extraction_guest_limit: int = Field(default=5, ge=1, le=5)
    extraction_daily_limit: int = Field(default=25, ge=1, le=25)
    extraction_timeout_seconds: int = Field(default=30, ge=1, le=60)
    request_body_limit: int = Field(default=131072, ge=1, le=131072)
    api_address_limit: int = Field(default=120, ge=1, le=120)
    api_global_limit: int = Field(default=1200, ge=1, le=1200)
    guest_address_limit: int = Field(default=5, ge=1, le=5)
    guest_global_limit: int = Field(default=100, ge=1, le=100)
    workspace_limit: int = Field(default=1000, ge=1, le=1000)
    workspace_order_limit: int = Field(default=100, ge=1, le=100)
    workspace_customer_limit: int = Field(default=100, ge=1, le=100)
    workspace_product_limit: int = Field(default=100, ge=1, le=100)
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

settings = Settings()
