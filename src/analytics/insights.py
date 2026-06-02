"""
src/analytics/insights.py
--------------------------
Narrative insight engine. Generates human-readable, personalized insights
from pre-computed KPI dicts and raw DataFrames.

Design philosophy:
  - Each insight is a self-contained function that returns a dict
    with 'text', 'category', and 'strength' (how interesting/strong the signal is).
  - The orchestrator collects all insights, sorts by strength, and returns top N.
  - No hardcoded strings in the orchestrator — all copy lives in constants.py INSIGHT_TEMPLATES.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from config.constants import INSIGHT_TEMPLATES

logger = logging.getLogger(__name__)

# Insight categories for filtering/grouping in the UI
CATEGORIES = {
    "TASTE": "🎭 Taste",
    "DISCOVERY": "🔍 Discovery",
    "BEHAVIOR": "🧠 Behavior",
    "MOOD": "💫 Mood",
    "TREND": "📈 Trend",
}


def _insight(text: str, category: str, strength: float) -> dict[str, Any]:
    """Factory for a single insight record."""
    return {"text": text, "category": category, "strength": round(strength, 2)}


# ── Individual insight generators ─────────────────────────────────────────────

def insight_top_artist_dominance(df: pd.DataFrame) -> dict | None:
    if "artist" not in df.columns or df.empty:
        return None
    counts = df["artist"].value_counts()
    top_artist = counts.index[0]
    pct = counts.iloc[0] / len(df) * 100
    if pct >= 15:
        text = INSIGHT_TEMPLATES["top_artist_dominant"].format(
            artist=top_artist, pct=pct
        )
        return _insight(text, CATEGORIES["TASTE"], strength=pct / 100)
    return None


def insight_mainstream_vs_underground(df: pd.DataFrame) -> dict | None:
    if "popularity" not in df.columns or df.empty:
        return None
    avg = df["popularity"].mean()
    if avg >= 70:
        text = INSIGHT_TEMPLATES["mainstream_listener"].format(avg=avg)
        return _insight(text, CATEGORIES["TASTE"], strength=avg / 100)
    elif avg <= 40:
        text = INSIGHT_TEMPLATES["underground_listener"].format(avg=avg)
        return _insight(text, CATEGORIES["DISCOVERY"], strength=1 - avg / 100)
    return None


def insight_energy_profile(df: pd.DataFrame) -> dict | None:
    if "energy" not in df.columns or df.empty:
        return None
    avg = df["energy"].mean() * 100
    if avg >= 70:
        text = INSIGHT_TEMPLATES["high_energy"].format(avg=avg)
        return _insight(text, CATEGORIES["MOOD"], strength=avg / 100)
    elif avg <= 35:
        text = (
            f"Your listening skews low-energy ({avg:.0f}/100). "
            "You're gravitating toward music that settles rather than activates."
        )
        return _insight(text, CATEGORIES["MOOD"], strength=1 - avg / 100)
    return None


def insight_valence_profile(df: pd.DataFrame) -> dict | None:
    if "valence" not in df.columns or df.empty:
        return None
    avg = df["valence"].mean() * 100
    if avg >= 65:
        text = INSIGHT_TEMPLATES["high_valence"].format(avg=avg)
        return _insight(text, CATEGORIES["MOOD"], strength=avg / 100)
    elif avg <= 35:
        text = (
            f"Your average valence is {avg:.0f}/100 — you're drawn to darker, "
            "more melancholic sounds right now."
        )
        return _insight(text, CATEGORIES["MOOD"], strength=1 - avg / 100)
    return None


def insight_genre_concentration(artists_df: pd.DataFrame) -> dict | None:
    if artists_df is None or artists_df.empty or "genres" not in artists_df.columns:
        return None
    genre_series = artists_df["genres"].dropna()
    all_genres = [
        g.strip()
        for row in genre_series
        for g in str(row).split(",")
        if g.strip()
    ]
    if not all_genres:
        return None
    counts = pd.Series(all_genres).value_counts()
    top_genre = counts.index[0]
    top_pct = counts.iloc[0] / sum(counts) * 100
    total_genres = len(counts)

    if top_pct >= 40:
        text = INSIGHT_TEMPLATES["low_diversity"].format(
            top_genre=top_genre, pct=top_pct
        )
        return _insight(text, CATEGORIES["TASTE"], strength=top_pct / 100)
    elif total_genres >= 10:
        text = INSIGHT_TEMPLATES["high_diversity"].format(
            score=0.8,  # placeholder if full diversity score not passed
            genre_count=total_genres,
        )
        return _insight(text, CATEGORIES["DISCOVERY"], strength=total_genres / 20)
    return None


def insight_acousticness(df: pd.DataFrame) -> dict | None:
    if "acousticness" not in df.columns or df.empty:
        return None
    avg = df["acousticness"].mean() * 100
    if avg >= 60:
        return _insight(
            f"Your music is predominantly acoustic ({avg:.0f}/100). "
            "You're choosing organic, unprocessed sounds over heavy production.",
            CATEGORIES["TASTE"],
            strength=avg / 100,
        )
    elif avg <= 20:
        return _insight(
            f"Your sound palette is heavily produced — low acousticness ({avg:.0f}/100). "
            "Electronic, synthesized textures dominate your listening.",
            CATEGORIES["TASTE"],
            strength=1 - avg / 100,
        )
    return None


def insight_danceability(df: pd.DataFrame) -> dict | None:
    if "danceability" not in df.columns or df.empty:
        return None
    avg = df["danceability"].mean() * 100
    if avg >= 70:
        return _insight(
            f"High danceability score ({avg:.0f}/100). Your playlist would not disappoint at a party.",
            CATEGORIES["BEHAVIOR"],
            strength=avg / 100,
        )
    return None


def insight_instrumentalness(df: pd.DataFrame) -> dict | None:
    if "instrumentalness" not in df.columns or df.empty:
        return None
    avg = df["instrumentalness"].mean()
    if avg >= 0.4:
        return _insight(
            f"Roughly {avg*100:.0f}% of your listening is instrumental. "
            "You're using music as a focus environment, not just entertainment.",
            CATEGORIES["BEHAVIOR"],
            strength=avg,
        )
    return None


def insight_explicit_ratio(df: pd.DataFrame) -> dict | None:
    if "explicit" not in df.columns or df.empty:
        return None
    pct = df["explicit"].mean() * 100
    if pct >= 50:
        return _insight(
            f"{pct:.0f}% of your top tracks are explicit. "
            "You're not filtering for content — you're listening for the art.",
            CATEGORIES["BEHAVIOR"],
            strength=pct / 100,
        )
    elif pct <= 5:
        return _insight(
            f"Almost none of your top tracks are explicit ({pct:.0f}%). "
            "You're skewing toward clean, accessible music.",
            CATEGORIES["BEHAVIOR"],
            strength=1 - pct / 100,
        )
    return None


def insight_decade_distribution(df: pd.DataFrame) -> dict | None:
    if "release_date" not in df.columns or df.empty:
        return None
    years = pd.to_datetime(df["release_date"].dropna(), errors="coerce").dt.year.dropna()
    if years.empty:
        return None
    decades = (years // 10 * 10).astype(int)
    top_decade = decades.value_counts().index[0]
    pct = decades.value_counts().iloc[0] / len(decades) * 100

    decade_str = f"{top_decade}s"
    if top_decade == 2020:
        decade_str = "the current decade"
    elif top_decade <= 1990:
        decade_str = f"the {top_decade}s — a classic era"

    return _insight(
        f"Your listening gravitates toward {decade_str} ({pct:.0f}% of tracks). "
        "This decade clearly shaped your musical identity.",
        CATEGORIES["TASTE"],
        strength=pct / 100,
    )


# ── Orchestrator ───────────────────────────────────────────────────────────────

def generate_insights(
    tracks_df: pd.DataFrame,
    artists_df: pd.DataFrame | None = None,
    top_n: int = 6,
) -> list[dict[str, Any]]:
    """
    Run all insight generators and return the top N by signal strength.
    """
    candidates = [
        insight_top_artist_dominance(tracks_df),
        insight_mainstream_vs_underground(tracks_df),
        insight_energy_profile(tracks_df),
        insight_valence_profile(tracks_df),
        insight_acousticness(tracks_df),
        insight_danceability(tracks_df),
        insight_instrumentalness(tracks_df),
        insight_explicit_ratio(tracks_df),
        insight_decade_distribution(tracks_df),
    ]

    if artists_df is not None:
        candidates.append(insight_genre_concentration(artists_df))

    valid = [c for c in candidates if c is not None]
    valid.sort(key=lambda x: x["strength"], reverse=True)
    logger.debug("Generated %d insights, returning top %d", len(valid), top_n)
    return valid[:top_n]
