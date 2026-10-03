"""
PocketSmart AI — Central Configuration
All application settings loaded from environment variables.
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "PocketSmart AI"
    debug: bool = True

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # JWT
    secret_key: str = "pocketsmart-fallback-secret-key-change-in-production-2024"
    access_token_expire_minutes: int = 10080  # 7 days
    algorithm: str = "HS256"

    # CORS
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
