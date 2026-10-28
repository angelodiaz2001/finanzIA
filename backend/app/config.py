"""Configuración del backend principal (variables de entorno / archivo .env)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "FinanzIA API"
    # Sin .env se usa SQLite local para facilitar el arranque; el objetivo del
    # proyecto es MySQL (ver docker-compose.yml y .env.example).
    database_url: str = "sqlite:///./finanzia.db"

    # URLs de las tres APIs simuladas. Se usa 127.0.0.1 en lugar de localhost
    # porque en Windows "localhost" intenta primero IPv6 y añade segundos de espera.
    bank_api_url: str = "http://127.0.0.1:8001"
    wallet_api_url: str = "http://127.0.0.1:8002"
    notifications_api_url: str = "http://127.0.0.1:8003"
    source_timeout_seconds: float = 10.0

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    default_currency: str = "PEN"

    # Reglas de integración
    notification_min_confidence: float = 0.6
    dedup_window_hours: int = 36
    dedup_similarity_threshold: float = 0.5

    # IA generativa (opcional)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: str = "medium"
    anthropic_server_fallback: bool = True
    anthropic_max_tool_rounds: int = 8

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
