"""
Central configuration for the CareConfide backend.

All secrets come from environment variables. Nothing here is hardcoded.
If Supabase or the AI API key are not configured, the app degrades
gracefully (in-memory demo store / mock AI) rather than crashing, so the
hackathon demo always runs.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_secret_key: str = os.getenv("SUPABASE_SECRET_KEY", "")

    ai_api_key: str = os.getenv("AI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "claude-sonnet-4-6")

    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_secret_key)

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
