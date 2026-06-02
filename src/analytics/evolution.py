"""
src/analytics/evolution.py
--------------------------
Taste evolution analysis: detect drift, emerging artists, and genre pivots
across short / medium / long-term listening profiles.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

TIME_ORDER = ["short_term", "medium_term", "long_term"]


def compare_time_ranges(
    dfs: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """
    Given a dict of {time_range: DataFrame}, compute:
      - Artists that appear in short_term but not long_term (emerging)
      - Artists that appear in long_term but not short_term (fading)
      - Popularity trend direction
      - Energy/valence shift direction
      - Tracks that appear across all ranges (your true constants)
    """
    available = [t for t in TIME_ORDER if t in dfs and not dfs[t].empty]
    if len(available) < 2:
        return {"error": "Need at least 2 time ranges to compare"}

    short = dfs.get("short_term", pd.DataFrame())
    medium = dfs.get("medium_term", pd.DataFrame())
    long = dfs.get("long_term", pd.DataFrame())

    results: dict[str, Any] = {}

    # ── Artist emergence / fading ──────────────────────────────────────────
    if not short.empty and not long.empty and "artist" in short.columns:
        short_artists = set(short["artist"].dropna().unique())
        long_artists = set(long["artist"].dropna().unique())
        medium_artists = (
            set(medium["artist"].dropna().unique())
            if not medium.empty and "artist" in medium.columns
            else set()
        )

        results["emerging_artists"] = sorted(short_artists - long_artists)
        results["fading_artists"] = sorted(long_artists - short_artists)
        results["consistent_artists"] = sorted(short_artists & long_artists)

        if medium_artists:
            results["new_to_medium"] = sorted(medium_artists - long_artists)

    # ── Track constants (in all ranges) ───────────────────────────────────
    if all(
        not dfs[t].empty and "track_id" in dfs[t].columns
        for t in available
    ):
        id_sets = [set(dfs[t]["track_id"].dropna().unique()) for t in available]
        universal_ids = id_sets[0].intersection(*id_sets[1:])
        if not short.empty and "track_id" in short.columns:
            universal_tracks = short[short["track_id"].isin(universal_ids)][
                ["track_name", "artist"]
            ].drop_duplicates()
            results["universal_tracks"] = universal_tracks.to_dict("records")

    # ── Feature drift ──────────────────────────────────────────────────────
    feature_drift = {}
    for feat in ["popularity", "energy", "valence", "danceability", "acousticness"]:
        per_range = {}
        for t in available:
            df = dfs[t]
            if feat in df.columns and not df[feat].isna().all():
                per_range[t] = round(float(df[feat].mean()), 3)
        if len(per_range) >= 2:
            feature_drift[feat] = per_range

    results["feature_drift"] = feature_drift

    # ── Drift direction summary ────────────────────────────────────────────
    drift_summary = []
    for feat, values in feature_drift.items():
        ordered = [values[t] for t in available if t in values]
        if len(ordered) >= 2:
            delta = ordered[0] - ordered[-1]  # short vs long
            if abs(delta) > 0.05:
                direction = "increasing" if delta < 0 else "decreasing"
                drift_summary.append(
                    f"{feat.capitalize()} is {direction} over time "
                    f"(Δ {abs(delta):.2f})"
                )
    results["drift_summary"] = drift_summary

    return results


def build_rank_evolution_df(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build a long-format DataFrame for bump chart visualization.
    Columns: track_name, artist, time_range, rank, track_id
    """
    frames = []
    for time_range, df in dfs.items():
        if df.empty or "rank" not in df.columns:
            continue
        cols = ["rank", "track_name", "artist"]
        if "track_id" in df.columns:
            cols.append("track_id")
        sub = df[cols].copy()
        sub["time_range"] = time_range
        frames.append(sub)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["time_range_order"] = combined["time_range"].map(
        {t: i for i, t in enumerate(TIME_ORDER)}
    )
    return combined.sort_values(["time_range_order", "rank"])


def calculate_rank_velocity(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    For tracks that appear in both short and long term:
    rank_velocity = long_rank - short_rank (positive = climbed, negative = fell)
    """
    if "short_term" not in dfs or "long_term" not in dfs:
        return pd.DataFrame()
    if dfs["short_term"].empty or dfs["long_term"].empty:
        return pd.DataFrame()

    short = dfs["short_term"][["track_id", "track_name", "artist", "rank"]].copy()
    long_ = dfs["long_term"][["track_id", "rank"]].copy()

    merged = short.merge(long_, on="track_id", suffixes=("_short", "_long"))
    merged["rank_change"] = merged["rank_long"] - merged["rank_short"]
    merged["direction"] = merged["rank_change"].apply(
        lambda x: "↑ Rising" if x > 0 else ("↓ Falling" if x < 0 else "→ Stable")
    )
    return merged.sort_values("rank_change", ascending=False)
