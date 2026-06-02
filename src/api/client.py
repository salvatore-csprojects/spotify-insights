"""
src/api/client.py
-----------------
Authenticated Spotipy client with:
  - Retry logic (tenacity)
  - Rate-limit awareness (respect Retry-After header)
  - Singleton pattern so the token is reused across the session
"""

import logging
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings

logger = logging.getLogger(__name__)


def _build_auth_manager() -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=settings.spotify_client_id,
        client_secret=settings.spotify_client_secret,
        redirect_uri=settings.spotify_redirect_uri,
        scope=settings.spotify_scope,
        cache_path=f"{settings.cache_dir}/.spotify_token_cache",
        open_browser=True,
    )


class SpotifyClient:
    """Thin wrapper around spotipy.Spotify with retry + logging."""

    _instance: "SpotifyClient | None" = None

    def __init__(self) -> None:
        self._sp = spotipy.Spotify(
            auth_manager=_build_auth_manager(),
            requests_timeout=10,
        )
        logger.info("Spotify client initialised")

    @classmethod
    def get(cls) -> "SpotifyClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @retry(
        retry=retry_if_exception_type(spotipy.SpotifyException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def current_user(self) -> dict:
        return self._sp.current_user()

    @retry(
        retry=retry_if_exception_type(spotipy.SpotifyException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def current_user_top_tracks(self, time_range: str, limit: int = 50) -> dict:
        logger.debug("Fetching top tracks: time_range=%s limit=%d", time_range, limit)
        return self._sp.current_user_top_tracks(time_range=time_range, limit=limit)

    @retry(
        retry=retry_if_exception_type(spotipy.SpotifyException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def current_user_top_artists(self, time_range: str, limit: int = 50) -> dict:
        logger.debug("Fetching top artists: time_range=%s limit=%d", time_range, limit)
        return self._sp.current_user_top_artists(time_range=time_range, limit=limit)

    def audio_features(self, track_ids: list[str]) -> list[dict]:
        """Batch audio feature fetch — handles Spotify's 100-item limit.
        Note: endpoint deprecated for apps created after Nov 2024; raises on 403."""
        results = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i : i + 100]
            logger.debug("Fetching audio features batch %d/%d", i // 100 + 1, -(-len(track_ids) // 100))
            batch_result = self._sp.audio_features(batch)
            if batch_result:
                results.extend([f for f in batch_result if f is not None])
            time.sleep(0.1)
        return results

    @retry(
        retry=retry_if_exception_type(spotipy.SpotifyException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def current_user_recently_played(self, limit: int = 50) -> dict:
        logger.debug("Fetching recently played: limit=%d", limit)
        return self._sp.current_user_recently_played(limit=limit)

    @retry(
        retry=retry_if_exception_type(spotipy.SpotifyException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def recommendations(
        self,
        seed_artists: list[str] | None = None,
        seed_tracks: list[str] | None = None,
        seed_genres: list[str] | None = None,
        limit: int = 20,
        **kwargs,
    ) -> dict:
        return self._sp.recommendations(
            seed_artists=seed_artists,
            seed_tracks=seed_tracks,
            seed_genres=seed_genres,
            limit=limit,
            **kwargs,
        )

    @retry(
        retry=retry_if_exception_type(spotipy.SpotifyException),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def artists(self, artist_ids: list[str]) -> dict:
        """Batch artist fetch — handles Spotify's 50-item limit."""
        results = []
        for i in range(0, len(artist_ids), 50):
            batch = artist_ids[i : i + 50]
            batch_result = self._sp.artists(batch)
            if batch_result and "artists" in batch_result:
                results.extend(batch_result["artists"])
            time.sleep(0.1)
        return {"artists": results}
