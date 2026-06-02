"""
config/settings.py
------------------
Centralised, validated configuration using Pydantic BaseSettings.
All values are env-driven; no magic strings scattered across the codebase.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Spotify OAuth ──────────────────────────────────────────────────────
    spotify_client_id: str = Field(..., env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(..., env="SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str = Field(
        "http://127.0.0.1:8888/callback", env="SPOTIFY_REDIRECT_URI"
    )

    # ── Spotify API scope ──────────────────────────────────────────────────
    # Extend this when you add new endpoints (e.g. playlist-read-private)
    spotify_scope: str = (
        "user-top-read "
        "user-read-recently-played "
        "user-library-read "
        "playlist-read-private"
    )

    # ── ETL settings ───────────────────────────────────────────────────────
    time_ranges: list[Literal["short_term", "medium_term", "long_term"]] = [
        "short_term",
        "medium_term",
        "long_term",
    ]
    top_tracks_limit: int = Field(50, ge=1, le=50)   # Spotify API max = 50
    recently_played_limit: int = Field(50, ge=1, le=50)

    # ── Paths ──────────────────────────────────────────────────────────────
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"
    cache_dir: str = ".cache"
    log_dir: str = "logs"

    # ── Caching ────────────────────────────────────────────────────────────
    cache_ttl_seconds: int = Field(3600, description="1-hour default TTL")

    # ── Analytics thresholds ───────────────────────────────────────────────
    mainstream_popularity_threshold: int = Field(
        70, description="Tracks above this are 'mainstream'"
    )
    obscure_popularity_threshold: int = Field(
        30, description="Tracks below this are 'obscure'"
    )

    # ── Logging ────────────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("spotify_client_id", "spotify_client_secret")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Spotify credentials must not be empty")
        return v.strip()

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Module-level shortcut so callers can just: from config.settings import settings
settings = get_settings()
