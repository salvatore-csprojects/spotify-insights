"""
src/analytics/kpis.py
---------------------
Core KPI calculations. All functions are pure — they take a DataFrame
and return a dict or scalar. No side effects.
"""

from __future__ import annotations

import math
import logging
from typing import Any

import numpy as np
import pandas as pd

from config.constants import (
    ANALYSIS_FEATURES,
    DIVERSITY_BANDS,
    MOOD_ARCHETYPES,
    POPULARITY_BUCKETS,
)

logger = logging.getLogger(__name__)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _safe_mean(series: pd.Series, decimals: int = 1) -> float:
    """Mean that handles empty / all-NaN series gracefully."""
    if series.empty or series.isna().all():
        return 0.0
    return round(float(series.mean()), decimals)


def _format_duration(ms: float) -> str:
    """Convert milliseconds to mm:ss string."""
    seconds = int(ms / 1000)
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


# ── Core track KPIs ────────────────────────────────────────────────────────────

def calculate_track_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """
    Main KPI bundle for the Overview page.
    Returns a flat dict of display-ready values.
    """
    if df.empty:
        return {}

    # Basic counts
    total_tracks = len(df)
    unique_artists = df["artist"].nunique() if "artist" in df.columns else 0
    unique_albums = df["album"].nunique() if "album" in df.columns else 0

    # Popularity
    avg_popularity = _safe_mean(df.get("popularity", pd.Series(dtype=float)))
    max_popularity = int(df["popularity"].max()) if "popularity" in df.columns else 0
    min_popularity = int(df["popularity"].min()) if "popularity" in df.columns else 0

    # Duration
    avg_duration_ms = _safe_mean(df.get("duration_ms", pd.Series(dtype=float)), 0)
    avg_duration_fmt = _format_duration(avg_duration_ms) if avg_duration_ms else "N/A"
    total_listen_time_hrs = round(
        df["duration_ms"].sum() / (1000 * 60 * 60), 1
    ) if "duration_ms" in df.columns else 0.0

    # Audio feature averages
    audio_avgs = {
        f"avg_{feat}": _safe_mean(df[feat]) if feat in df.columns else None
        for feat in ANALYSIS_FEATURES
    }

    # Popularity category distribution
    pop_dist = categorize_popularity(df)

    # Explicit ratio
    explicit_pct = round(
        df["explicit"].mean() * 100, 1
    ) if "explicit" in df.columns else None

    return {
        "total_tracks": total_tracks,
        "unique_artists": unique_artists,
        "unique_albums": unique_albums,
        "avg_popularity": avg_popularity,
        "max_popularity": max_popularity,
        "min_popularity": min_popularity,
        "avg_duration": avg_duration_fmt,
        "avg_duration_ms": avg_duration_ms,
        "total_listen_time_hrs": total_listen_time_hrs,
        "explicit_pct": explicit_pct,
        "popularity_distribution": pop_dist,
        **audio_avgs,
    }


# ── Popularity ─────────────────────────────────────────────────────────────────

def categorize_popularity(df: pd.DataFrame) -> dict[str, int]:
    """Return count of tracks per popularity bucket."""
    if "popularity" not in df.columns:
        return {}
    result = {}
    for label, (lo, hi) in POPULARITY_BUCKETS.items():
        result[label] = int(((df["popularity"] >= lo) & (df["popularity"] <= hi)).sum())
    return result


# ── Diversity Score ────────────────────────────────────────────────────────────

def calculate_diversity_score(
    tracks_df: pd.DataFrame,
    artists_df: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """
    Composite diversity score (0–1) using Shannon entropy across three axes:
      1. Genre distribution (from artists_df if available, else skipped)
      2. Popularity tier distribution
      3. Release decade distribution

    Returns score + label + per-axis scores.
    """
    scores = []

    # Axis 1: Genre diversity (needs artists_df with genres column)
    genre_entropy = None
    if artists_df is not None and not artists_df.empty and "genres" in artists_df.columns:
        genre_series = artists_df["genres"].dropna()
        if not genre_series.empty:
            all_genres = [
                g.strip()
                for row in genre_series
                for g in str(row).split(",")
                if g.strip()
            ]
            genre_counts = pd.Series(all_genres).value_counts(normalize=True)
            genre_entropy = _normalized_entropy(genre_counts.values)
            scores.append(genre_entropy)

    # Axis 2: Popularity tier diversity
    pop_entropy = None
    if "popularity" in tracks_df.columns:
        bins = [0, 20, 40, 60, 80, 100]
        labels_bins = ["0–20", "20–40", "40–60", "60–80", "80–100"]
        bucketed = pd.cut(
            tracks_df["popularity"].dropna(),
            bins=bins,
            labels=labels_bins,
            include_lowest=True,
        )
        if not bucketed.empty:
            probs = bucketed.value_counts(normalize=True).values
            pop_entropy = _normalized_entropy(probs)
            scores.append(pop_entropy)

    # Axis 3: Release decade diversity
    decade_entropy = None
    if "release_date" in tracks_df.columns:
        years = pd.to_datetime(
            tracks_df["release_date"].dropna(), errors="coerce"
        ).dt.year.dropna()
        if not years.empty:
            decades = (years // 10 * 10).astype(int)
            probs = decades.value_counts(normalize=True).values
            decade_entropy = _normalized_entropy(probs)
            scores.append(decade_entropy)

    composite = round(sum(scores) / len(scores), 3) if scores else 0.0

    label, emoji = "N/A", "❓"
    for lo, hi, lbl, em in DIVERSITY_BANDS:
        if lo <= composite < hi or (hi == 1.0 and composite == 1.0):
            label, emoji = lbl, em
            break

    return {
        "score": composite,
        "label": label,
        "emoji": emoji,
        "genre_entropy": round(genre_entropy, 3) if genre_entropy is not None else None,
        "popularity_entropy": round(pop_entropy, 3) if pop_entropy is not None else None,
        "decade_entropy": round(decade_entropy, 3) if decade_entropy is not None else None,
    }


def _normalized_entropy(probs: np.ndarray) -> float:
    """Shannon entropy normalized to [0, 1] using log2(n) as max."""
    probs = probs[probs > 0]
    if len(probs) <= 1:
        return 0.0
    raw = -np.sum(probs * np.log2(probs))
    max_entropy = math.log2(len(probs))
    return float(raw / max_entropy) if max_entropy > 0 else 0.0


# ── Artist Concentration ───────────────────────────────────────────────────────

def calculate_concentration_index(df: pd.DataFrame) -> dict[str, Any]:
    """
    Herfindahl-Hirschman Index (HHI) for artist concentration.
    0.0 = perfectly distributed, 1.0 = single-artist dominance.
    """
    if "artist" not in df.columns or df.empty:
        return {"hhi": 0.0, "label": "N/A", "top_artist_share": 0.0}

    shares = df["artist"].value_counts(normalize=True)
    hhi = float((shares**2).sum())
    top_artist = shares.index[0]
    top_share = round(float(shares.iloc[0]) * 100, 1)

    if hhi < 0.1:
        label = "Very Eclectic"
    elif hhi < 0.2:
        label = "Balanced"
    elif hhi < 0.4:
        label = "Somewhat Concentrated"
    else:
        label = "Dominant Artist Phase"

    return {
        "hhi": round(hhi, 3),
        "label": label,
        "top_artist": top_artist,
        "top_artist_share_pct": top_share,
    }


# ── Mood Archetype ─────────────────────────────────────────────────────────────

def detect_mood_archetype(df: pd.DataFrame) -> dict[str, Any]:
    """
    Classify dominant mood based on average valence + energy.
    Returns best-matching archetype name and characteristics.
    """
    if "valence" not in df.columns or "energy" not in df.columns:
        return {"archetype": "Unknown", "description": "No audio features available"}

    avg_valence = df["valence"].mean()
    avg_energy = df["energy"].mean()

    for name, bounds in MOOD_ARCHETYPES.items():
        v_lo, v_hi = bounds["valence"]
        e_lo, e_hi = bounds["energy"]
        if v_lo <= avg_valence <= v_hi and e_lo <= avg_energy <= e_hi:
            return {
                "archetype": name,
                "avg_valence": round(avg_valence, 2),
                "avg_energy": round(avg_energy, 2),
            }

    # Fallback: closest match
    return {
        "archetype": "Balanced Flow",
        "avg_valence": round(avg_valence, 2),
        "avg_energy": round(avg_energy, 2),
    }


# ── Audio feature summary ──────────────────────────────────────────────────────

def calculate_audio_profile(df: pd.DataFrame) -> dict[str, float]:
    """
    Returns normalized (0–1) averages for radar chart display.
    Tempo is normalized against a 200bpm ceiling.
    Loudness (typically -60 to 0 dB) normalized to 0–1.
    """
    profile = {}
    for feat in ANALYSIS_FEATURES:
        if feat in df.columns:
            profile[feat] = round(float(df[feat].mean()), 3)

    # Normalize tempo
    if "tempo" in df.columns:
        profile["tempo_normalized"] = round(
            min(float(df["tempo"].mean()) / 200.0, 1.0), 3
        )

    # Normalize loudness: typical range -60 to 0 dB → 0 to 1
    if "loudness" in df.columns:
        raw_loudness = float(df["loudness"].mean())
        profile["loudness_normalized"] = round(
            max(0.0, min(1.0, (raw_loudness + 60) / 60)), 3
        )

    return profile
