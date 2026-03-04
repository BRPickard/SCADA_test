from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    app_name: str = "Dynamic SCADA Master Plan Tool"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./scada.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")
    master_key: str = os.getenv("MASTER_KEY", "local-master-key")
    demo_mode: bool = os.getenv("DEMO_MODE", "true").lower() == "true"


@lru_cache
def get_settings() -> Settings:
    return Settings()
