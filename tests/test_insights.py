"""
tests/test_insights.py
-----------------------
Unit tests for analytics/insights.py narrative engine.
"""

import pandas as pd
import pytest

from src.analytics.insights import (
    generate_insights,
    insight_top_artist_dominance,
    insight_mainstream_vs_underground,
    insight_energy_profile,
    insight_valence_profile,
    insight_decade_distribution,
)


@pytest.fixture
def mainstream_df():
    return pd.DataFrame(
        {
            "artist": ["Pop Star"] * 8 + ["Other"] * 2,
            "popularity": [85, 90, 88, 82, 91, 78, 86, 87, 50, 45],
            "energy": [0.75] * 10,
            "valence": [0.7] * 10,
            "acousticness": [0.1] * 10,
            "release_date": ["2023-05-01"] * 10,
            "explicit": [False] * 10,
        }
    )


@pytest.fixture
def underground_df():
    return pd.DataFrame(
        {
            "artist": [f"Artist {i}" for i in range(10)],
            "popularity": [20, 25, 15, 30, 18, 22, 28, 12, 35, 27],
            "energy": [0.8] * 10,
            "valence": [0.2] * 10,
            "acousticness": [0.05] * 10,
            "release_date": ["2021-01-01"] * 10,
            "explicit": [True] * 10,
        }
    )


class TestIndividualInsights:
    def test_dominant_artist_fires_above_15pct(self, mainstream_df):
        # Pop Star = 80% share → should fire
        result = insight_top_artist_dominance(mainstream_df)
        assert result is not None
        assert "Pop Star" in result["text"]

    def test_dominant_artist_silent_when_distributed(self, underground_df):
        # All different artists, each 10% → should not fire
        result = insight_top_artist_dominance(underground_df)
        assert result is None

    def test_mainstream_insight_fires(self, mainstream_df):
        result = insight_mainstream_vs_underground(mainstream_df)
        assert result is not None
        assert "mainstream" in result["text"].lower() or "85" in result["text"] or "84" in result["text"]

    def test_underground_insight_fires(self, underground_df):
        result = insight_mainstream_vs_underground(underground_df)
        assert result is not None
        assert "underground" in result["text"].lower() or "haven't" in result["text"].lower()

    def test_high_energy_fires(self):
        df = pd.DataFrame({"energy": [0.85] * 10})
        result = insight_energy_profile(df)
        assert result is not None
        assert result["category"].endswith("Mood")

    def test_energy_neutral_returns_none(self):
        df = pd.DataFrame({"energy": [0.5] * 10})
        result = insight_energy_profile(df)
        assert result is None

    def test_decade_insight_fires(self, mainstream_df):
        result = insight_decade_distribution(mainstream_df)
        assert result is not None
        assert "2020s" in result["text"] or "decade" in result["text"].lower()

    def test_missing_column_returns_none(self):
        df = pd.DataFrame({"track_name": ["A", "B"]})
        assert insight_top_artist_dominance(df) is None
        assert insight_mainstream_vs_underground(df) is None
        assert insight_energy_profile(df) is None
        assert insight_valence_profile(df) is None


class TestGenerateInsights:
    def test_returns_list(self, mainstream_df):
        results = generate_insights(mainstream_df)
        assert isinstance(results, list)

    def test_top_n_respected(self, mainstream_df):
        results = generate_insights(mainstream_df, top_n=3)
        assert len(results) <= 3

    def test_sorted_by_strength(self, mainstream_df):
        results = generate_insights(mainstream_df, top_n=6)
        strengths = [r["strength"] for r in results]
        assert strengths == sorted(strengths, reverse=True)

    def test_each_insight_has_required_keys(self, mainstream_df):
        results = generate_insights(mainstream_df)
        for r in results:
            assert "text" in r
            assert "category" in r
            assert "strength" in r
            assert isinstance(r["text"], str)
            assert len(r["text"]) > 10

    def test_empty_df_returns_empty_list(self):
        results = generate_insights(pd.DataFrame())
        assert results == []

    def test_strength_between_0_and_1(self, mainstream_df):
        results = generate_insights(mainstream_df)
        for r in results:
            assert 0.0 <= r["strength"] <= 1.0
