"""Centralised, type-safe configuration.

All secrets/urls are loaded from the environment (`.env` in dev) via
pydantic-settings. Nothing is hardcoded; importing `settings` anywhere in the
app gives validated, cached values.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Supabase (trusted server access)
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: str = Field(alias="SUPABASE_JWT_SECRET", default="")

    # LLM (Phase 2)
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    llm_model: str = Field(default="gemini-1.5-flash", alias="LLM_MODEL")

    # Polar.sh
    polar_access_token: str = Field(default="", alias="POLAR_ACCESS_TOKEN")
    polar_organization_id: str = Field(default="", alias="POLAR_ORGANIZATION_ID")
    # 'sandbox' while testing, 'production' once you flip to a live Polar org.
    polar_server: str = Field(default="sandbox", alias="POLAR_SERVER")
    # Signing secret from the Polar webhook you register (Settings -> Webhooks).
    # Required in production — without it, webhook payloads cannot be trusted.
    polar_webhook_secret: str = Field(default="", alias="POLAR_WEBHOOK_SECRET")
    # Polar product IDs for each paid tier (Polar dashboard -> Products).
    polar_product_starter_id: str = Field(default="", alias="POLAR_PRODUCT_STARTER_ID")
    polar_product_growth_id: str = Field(default="", alias="POLAR_PRODUCT_GROWTH_ID")

    # GitHub App Integration
    github_app_id: str = Field(default="", alias="GITHUB_APP_ID")
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    github_private_key: str = Field(default="", alias="GITHUB_PRIVATE_KEY")

    # AWS Integration
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")

    # App
    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    app_env: str = Field(default="development", alias="APP_ENV")

    @property
    def cors_origins(self) -> list[str]:
        """Frontend origins allowed to call this API."""
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is parsed once per process."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
