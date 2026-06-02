"""
src/processing/cleaning.py
--------------------------
Data cleaning and enrichment functions.
All pure transformations — no I/O, no side effects.
"""

from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# ── Tracks ─────────────────────────────────────────────────────────────────────

def clean_tracks_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and enrich a raw tracks DataFrame.
    Operations:
      - Cast types
      - Compute derived columns (duration_min, release_year, popularity_category, era)
      - Remove duplicates
      - Validate numeric ranges
    """
    if df.empty:
        return df

    df = df.copy()

    # ── Type casting ───────────────────────────────────────────────────────
    if "popularity" in df.columns:
        df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").clip(0, 100)

    if "duration_ms" in df.columns:
        df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce")
        df["duration_min"] = (df["duration_ms"] / 60_000).round(2)

    if "explicit" in df.columns:
        df["explicit"] = df["explicit"].astype(bool)

    # ── Audio features: clip to [0, 1] ────────────────────────────────────
    audio_features_0_1 = [
        "danceability", "energy", "speechiness", "acousticness",
        "instrumentalness", "liveness", "valence",
    ]
    for feat in audio_features_0_1:
        if feat in df.columns:
            df[feat] = pd.to_numeric(df[feat], errors="coerce").clip(0, 1)

    # ── Release year ───────────────────────────────────────────────────────
    if "release_date" in df.columns:
        df["release_year"] = pd.to_datetime(
            df["release_date"].str[:4], format="%Y", errors="coerce"
        ).dt.year.astype("Int64")
        current_year = datetime.now().year
        df.loc[df["release_year"] > current_year, "release_year"] = pd.NA

    # ── Era tagging ────────────────────────────────────────────────────────
    if "release_year" in df.columns:
        df["era"] = df["release_year"].apply(_era_label)

    # ── Popularity category ────────────────────────────────────────────────
    if "popularity" in df.columns:
        df["popularity_category"] = df["popularity"].apply(_popularity_label)

    # ── Energy tier ────────────────────────────────────────────────────────
    if "energy" in df.columns:
        df["energy_tier"] = pd.cut(
            df["energy"],
            bins=[0, 0.33, 0.66, 1.0],
            labels=["Low", "Medium", "High"],
            include_lowest=True,
        )

    # ── Dedup ──────────────────────────────────────────────────────────────
    before = len(df)
    if "track_id" in df.columns:
        df = df.drop_duplicates(subset=["track_id"], keep="first")
    after = len(df)
    if before != after:
        logger.debug("Removed %d duplicate tracks", before - after)

    logger.info("Cleaned tracks: %d rows", len(df))
    return df.reset_index(drop=True)


def _popularity_label(pop: float) -> str:
    if pd.isna(pop):
        return "Unknown"
    pop = int(pop)
    if pop >= 90:
        return "Mega-hit (90–100)"
    elif pop >= 70:
        return "Mainstream (70–89)"
    elif pop >= 50:
        return "Mid-tier (50–69)"
    elif pop >= 30:
        return "Indie (30–49)"
    else:
        return "Underground (0–29)"


def _era_label(year) -> str:
    if pd.isna(year):
        return "Unknown"
    year = int(year)
    if year >= 2020:
        return "2020s"
    elif year >= 2010:
        return "2010s"
    elif year >= 2000:
        return "2000s"
    elif year >= 1990:
        return "1990s"
    elif year >= 1980:
        return "1980s"
    else:
        return "Pre-1980s"


# ── Artists ─────────────────────────────────────────────────────────────────────

def clean_artists_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "popularity" in df.columns:
        df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").clip(0, 100)

    if "followers" in df.columns:
        df["followers"] = pd.to_numeric(df["followers"], errors="coerce").astype("Int64")
        df["followers_fmt"] = df["followers"].apply(
            lambda x: f"{x/1_000_000:.1f}M" if pd.notna(x) and x >= 1_000_000
            else (f"{x/1_000:.0f}K" if pd.notna(x) and x >= 1_000 else str(x))
        )

    # Primary genre (first genre in the comma-separated list)
    if "genres" in df.columns:
        df["primary_genre"] = df["genres"].apply(
            lambda g: str(g).split(",")[0].strip() if pd.notna(g) and g != "nan" else "Unknown"
        )

    if "artist_id" in df.columns:
        df = df.drop_duplicates(subset=["artist_id"], keep="first")

    logger.info("Cleaned artists: %d rows", len(df))
    return df.reset_index(drop=True)


# ── Recently played ─────────────────────────────────────────────────────────────

def clean_recently_played(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "played_at" in df.columns:
        df["played_at"] = pd.to_datetime(df["played_at"], utc=True, errors="coerce")
        df["hour_of_day"] = df["played_at"].dt.hour
        df["day_of_week"] = df["played_at"].dt.day_name()
        df["date"] = df["played_at"].dt.date

    if "duration_ms" in df.columns:
        df["duration_min"] = (
            pd.to_numeric(df["duration_ms"], errors="coerce") / 60_000
        ).round(2)

    # Dedup: same track at same timestamp
    if "track_id" in df.columns and "played_at" in df.columns:
        df = df.drop_duplicates(subset=["track_id", "played_at"], keep="first")

    df = df.sort_values("played_at", ascending=False).reset_index(drop=True)
    logger.info("Cleaned recently played: %d rows", len(df))
    return df
