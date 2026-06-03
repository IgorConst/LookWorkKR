from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    korect_email: str
    korect_password: str
    database_url: str = "sqlite+aiosqlite:///./data/lwk.db"
    playwright_headless: bool = True
    scrape_interval_minutes: int = 30

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()