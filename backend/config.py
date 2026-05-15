from functools import lru_cache
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover
    from pydantic import BaseModel

    class BaseSettings(BaseModel):
        """Fallback settings base when pydantic-settings is unavailable."""

        def __init__(self, **data):
            super().__init__(**data)

    def SettingsConfigDict(**kwargs):
        return kwargs


ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    google_vision_api_key: str | None = None
    database_url: str | None = None
    env: str = "development"
    log_level: str = "INFO"
    max_image_size_mb: int = 10
    demo_mode: bool = True
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    supabase_url: str | None = None
    supabase_key: str | None = None
    supabase_analyses_table: str = "analyses"
    supabase_brands_table: str = "brands"
    model_path: Path = ROOT_DIR / "backend" / "ml" / "fabric_model.pkl"

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=(),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
