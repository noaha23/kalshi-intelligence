"""Central configuration loaded from environment variables / .env file."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Environment(StrEnum):
    DEMO = "demo"
    PRODUCTION = "production"


BASE_URLS = {
    Environment.DEMO: "https://demo-api.kalshi.co/trade-api/v2",
    Environment.PRODUCTION: "https://api.elections.kalshi.com/trade-api/v2",
}

WS_URLS = {
    Environment.DEMO: "wss://demo-api.kalshi.co/trade-api/ws/v2",
    Environment.PRODUCTION: "wss://api.elections.kalshi.com/trade-api/ws/v2",
}


class Settings(BaseSettings):
    """Application settings. All credentials come from env vars -- never hardcoded."""

    model_config = {"env_file": ".env", "env_prefix": "KALSHI_"}

    # Kalshi API
    environment: Environment = Environment.DEMO
    api_key_id: str = ""
    private_key_path: Path = Path("./keys/kalshi_private.pem")

    # AI providers (optional)
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    # Rate limits
    read_rate_limit: int = 20
    write_rate_limit: int = 10

    # Scanner defaults
    scan_min_volume_24h: int = 100
    scan_min_open_interest: int = 50
    scan_max_days_to_close: int = 90

    # Position sizing defaults
    max_position_pct: float = 0.05
    kelly_fraction: float = 0.25
    bankroll_cents: int = 100_000  # $1,000 default

    @property
    def base_url(self) -> str:
        return BASE_URLS[self.environment]

    @property
    def ws_url(self) -> str:
        return WS_URLS[self.environment]


@lru_cache
def get_settings() -> Settings:
    """Singleton accessor for settings."""
    return Settings()
