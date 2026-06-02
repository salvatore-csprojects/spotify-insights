"""
src/api/extract.py
------------------
All data extraction functions. Each returns a clean pandas DataFrame.
Side effects (saving to disk) are handled by the caller (main.py) or pipeline.
"""

import logging
from datetime import datetime, timezone

import pandas as pd

from src.api.client import SpotifyClient
from config.settings import settings

logger = logging.getLogger(__name__)


def extract_top_tracks(time_range: str) -> pd.DataFrame:
    """
    Extract user's top tracks for a given time range.
    Joins audio features in the same call to minimize round-trips.
    """
    client = SpotifyClient.get()
    resp = client.current_user_top_tracks(
        time_range=time_range, limit=settings.top_tracks_limit
    )
    items = resp.get("items", [])
    if not items:
        logger.warning("No top tracks returned for time_range=%s", time_range)
        return pd.DataFrame()

    rows = []
    for rank, track in enumerate(items, start=1):
        artists = track.get("artists", [])
        album = track.get("album", {})
        rows.append(
            {
                "rank": rank,
                "track_id": track["id"],
                "track_name": track["name"],
                "artist": artists[0]["name"] if artists else None,
                "artist_id": artists[0]["id"] if artists else None,
                "all_artists": ", ".join(a["name"] for a in artists),
                "album": album.get("name"),
                "album_id": album.get("id"),
                "release_date": album.get("release_date"),
                "popularity": track.get("popularity"),
                "duration_ms": track.get("duration_ms"),
                "explicit": track.get("explicit"),
                "external_url": track.get("external_urls", {}).get("spotify"),
                "preview_url": track.get("preview_url"),
                "time_range": time_range,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    df = pd.DataFrame(rows)

    # ── Join audio features (endpoint deprecated for new apps — skip on 403) ──
    track_ids = df["track_id"].tolist()
    try:
        audio_feats = client.audio_features(track_ids)
        if audio_feats:
            feat_df = pd.DataFrame(audio_feats).rename(columns={"id": "track_id"})
            feat_cols = [
                "track_id", "danceability", "energy", "key", "loudness", "mode",
                "speechiness", "acousticness", "instrumentalness", "liveness",
                "valence", "tempo", "time_signature",
            ]
            feat_df = feat_df[[c for c in feat_cols if c in feat_df.columns]]
            df = df.merge(feat_df, on="track_id", how="left")
    except Exception as e:
        logger.warning("Audio features unavailable (skipping): %s", e)

    logger.info(
        "Extracted %d top tracks for %s (%.0f%% with audio features)",
        len(df),
        time_range,
        df["danceability"].notna().mean() * 100 if "danceability" in df.columns else 0,
    )
    return df


def extract_top_artists(time_range: str) -> pd.DataFrame:
    """Extract user's top artists for a given time range, including genres."""
    client = SpotifyClient.get()
    resp = client.current_user_top_artists(
        time_range=time_range, limit=settings.top_tracks_limit
    )
    items = resp.get("items", [])
    if not items:
        return pd.DataFrame()

    rows = []
    for rank, artist in enumerate(items, start=1):
        rows.append(
            {
                "rank": rank,
                "artist_id": artist["id"],
                "artist_name": artist["name"],
                "genres": ", ".join(artist.get("genres", [])),
                "popularity": artist.get("popularity"),
                "followers": artist.get("followers", {}).get("total"),
                "external_url": artist.get("external_urls", {}).get("spotify"),
                "image_url": (
                    artist["images"][0]["url"] if artist.get("images") else None
                ),
                "time_range": time_range,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    df = pd.DataFrame(rows)
    logger.info("Extracted %d top artists for %s", len(df), time_range)
    return df


def extract_recently_played() -> pd.DataFrame:
    """Extract recently played tracks (up to 50, no time range filter)."""
    client = SpotifyClient.get()
    resp = client.current_user_recently_played(limit=settings.recently_played_limit)
    items = resp.get("items", [])
    if not items:
        return pd.DataFrame()

    rows = []
    seen = set()  # Dedup by (track_id, played_at) tuple
    for item in items:
        track = item.get("track", {})
        track_id = track.get("id")
        played_at = item.get("played_at")
        key = (track_id, played_at)
        if key in seen:
            continue
        seen.add(key)

        artists = track.get("artists", [])
        rows.append(
            {
                "track_id": track_id,
                "track_name": track.get("name"),
                "artist": artists[0]["name"] if artists else None,
                "artist_id": artists[0]["id"] if artists else None,
                "played_at": played_at,
                "duration_ms": track.get("duration_ms"),
                "popularity": track.get("popularity"),
                "explicit": track.get("explicit"),
                "external_url": track.get("external_urls", {}).get("spotify"),
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df["played_at"] = pd.to_datetime(df["played_at"], utc=True)
        df["hour_of_day"] = df["played_at"].dt.hour
        df["day_of_week"] = df["played_at"].dt.day_name()
    logger.info("Extracted %d recently played tracks", len(df))
    return df


def extract_user_profile() -> dict:
    """Extract user profile metadata."""
    client = SpotifyClient.get()
    user = client.current_user()
    return {
        "user_id": user.get("id"),
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "country": user.get("country"),
        "followers": user.get("followers", {}).get("total"),
        "image_url": (user["images"][0]["url"] if user.get("images") else None),
        "product": user.get("product"),  # free / premium
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }


def save_dataframe(df: pd.DataFrame, path: str) -> None:
    """Save a DataFrame to CSV, creating parent directories as needed."""
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Saved %d rows → %s", len(df), path)
