"""
Application configuration using Pydantic Settings.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Neo4j Configuration
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    neo4j_database: str

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Email Verification Configuration
    email_verification_expire_hours: int = 24

    # Email/SMTP Configuration
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int = 587
    mail_server: str
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    mail_from_name: str = "Momento"

    # Application Configuration
    app_name: str = "Momento"
    app_version: str = "0.1.0"

    # Model Provider Configuration
    extraction_provider: str = "local"
    extraction_allow_fallback: bool = False
    extraction_context_window_tokens: int = 128_000
    embedding_provider: str = "local"
    embedding_model: str = "text-embedding-3-small"

    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "gpt-oss:20b"
    ollama_timeout_seconds: int = 150
    ollama_max_retries: int = 2
    ollama_keep_alive: str = "5m"

    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-4.1"

    anthropic_api_key: Optional[str] = None
    anthropic_default_model: str = "claude-3-opus-20240229"

    # MCP / Integrations
    mcp_endpoint: Optional[str] = None
    mcp_api_key: Optional[str] = None

    # Security / Observability
    api_rate_limit_per_minute: int = 120
    enable_audit_logging: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
