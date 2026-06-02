"""
tests/test_kpis.py
------------------
Unit tests for analytics/kpis.py.
Run with: pytest tests/test_kpis.py -v
"""

import numpy as np
import pandas as pd
import pytest

from src.analytics.kpis import (
    calculate_audio_profile,
    calculate_concentration_index,
    calculate_diversity_score,
    calculate_track_kpis,
    detect_mood_archetype,
    _normalized_entropy,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_tracks_df():
    """Minimal realistic tracks DataFrame."""
    return pd.DataFrame(
        {
            "rank": range(1, 11),
            "track_id": [f"id_{i}" for i in range(10)],
            "track_name": [f"Track {i}" for i in range(10)],
            "artist": ["Artist A"] * 5 + ["Artist B"] * 3 + ["Artist C"] * 2,
            "album": [f"Album {i}" for i in range(10)],
            "release_date": ["2023-01-01"] * 5 + ["2021-06-15"] * 3 + ["2018-03-20"] * 2,
            "popularity": [80, 75, 60, 55, 90, 40, 35, 70, 25, 85],
            "duration_ms": [200_000] * 10,
            "explicit": [True, False] * 5,
            "danceability": np.linspace(0.3, 0.9, 10),
            "energy": np.linspace(0.5, 0.95, 10),
            "valence": np.linspace(0.2, 0.8, 10),
            "acousticness": np.linspace(0.1, 0.6, 10),
            "speechiness": [0.05] * 10,
            "instrumentalness": [0.01] * 10,
            "liveness": [0.12] * 10,
        }
    )


@pytest.fixture
def sample_artists_df():
    return pd.DataFrame(
        {
            "rank": range(1, 6),
            "artist_id": [f"art_{i}" for i in range(5)],
            "artist_name": [f"Artist {i}" for i in range(5)],
            "genres": [
                "pop, dance pop",
                "hip hop, rap",
                "rock, indie rock",
                "electronic, house",
                "r&b, soul",
            ],
            "popularity": [85, 70, 60, 55, 75],
            "followers": [1_000_000, 500_000, 200_000, 100_000, 750_000],
        }
    )


# ── calculate_track_kpis ───────────────────────────────────────────────────────

class TestCalculateTrackKpis:
    def test_returns_expected_keys(self, sample_tracks_df):
        kpis = calculate_track_kpis(sample_tracks_df)
        assert "total_tracks" in kpis
        assert "unique_artists" in kpis
        assert "avg_popularity" in kpis
        assert "total_listen_time_hrs" in kpis

    def test_total_tracks_count(self, sample_tracks_df):
        kpis = calculate_track_kpis(sample_tracks_df)
        assert kpis["total_tracks"] == 10

    def test_unique_artists(self, sample_tracks_df):
        kpis = calculate_track_kpis(sample_tracks_df)
        assert kpis["unique_artists"] == 3

    def test_avg_popularity_in_range(self, sample_tracks_df):
        kpis = calculate_track_kpis(sample_tracks_df)
        assert 0 <= kpis["avg_popularity"] <= 100

    def test_empty_df_returns_empty_dict(self):
        result = calculate_track_kpis(pd.DataFrame())
        assert result == {}

    def test_explicit_pct_calculation(self, sample_tracks_df):
        kpis = calculate_track_kpis(sample_tracks_df)
        # 5 True out of 10 = 50%
        assert kpis["explicit_pct"] == pytest.approx(50.0, abs=0.1)


# ── calculate_diversity_score ──────────────────────────────────────────────────

class TestDiversityScore:
    def test_score_between_0_and_1(self, sample_tracks_df, sample_artists_df):
        result = calculate_diversity_score(sample_tracks_df, sample_artists_df)
        assert 0.0 <= result["score"] <= 1.0

    def test_returns_label(self, sample_tracks_df):
        result = calculate_diversity_score(sample_tracks_df)
        assert isinstance(result["label"], str)
        assert len(result["label"]) > 0

    def test_single_artist_low_score(self):
        df = pd.DataFrame(
            {
                "artist": ["Same Artist"] * 20,
                "popularity": [80] * 20,
                "release_date": ["2023-01-01"] * 20,
            }
        )
        result = calculate_diversity_score(df)
        # Popularity entropy should be low (all same bucket)
        if result["popularity_entropy"] is not None:
            assert result["popularity_entropy"] < 0.3

    def test_normalized_entropy_uniform(self):
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = _normalized_entropy(probs)
        assert entropy == pytest.approx(1.0, abs=0.01)

    def test_normalized_entropy_single(self):
        probs = np.array([1.0])
        entropy = _normalized_entropy(probs)
        assert entropy == 0.0


# ── calculate_concentration_index ─────────────────────────────────────────────

class TestConcentrationIndex:
    def test_dominant_artist_high_hhi(self, sample_tracks_df):
        # Artist A has 5/10 = 50% share → HHI should be substantial
        result = calculate_concentration_index(sample_tracks_df)
        assert result["hhi"] > 0.1
        assert result["top_artist"] == "Artist A"

    def test_hhi_between_0_and_1(self, sample_tracks_df):
        result = calculate_concentration_index(sample_tracks_df)
        assert 0.0 <= result["hhi"] <= 1.0

    def test_empty_df(self):
        result = calculate_concentration_index(pd.DataFrame())
        assert result["hhi"] == 0.0

    def test_perfectly_distributed(self):
        df = pd.DataFrame(
            {"artist": [f"Artist {i}" for i in range(10)]}
        )
        result = calculate_concentration_index(df)
        # Each artist has 10% share → HHI = 10 × 0.01 = 0.1
        assert result["hhi"] == pytest.approx(0.1, abs=0.01)


# ── detect_mood_archetype ──────────────────────────────────────────────────────

class TestMoodArchetype:
    def test_euphoria_mode(self):
        df = pd.DataFrame({"valence": [0.8] * 5, "energy": [0.85] * 5})
        result = detect_mood_archetype(df)
        assert result["archetype"] == "Euphoria Mode"

    def test_dark_intensity(self):
        df = pd.DataFrame({"valence": [0.2] * 5, "energy": [0.8] * 5})
        result = detect_mood_archetype(df)
        assert result["archetype"] == "Dark Intensity"

    def test_sunday_chill(self):
        df = pd.DataFrame({"valence": [0.75] * 5, "energy": [0.25] * 5})
        result = detect_mood_archetype(df)
        assert result["archetype"] == "Sunday Chill"

    def test_missing_features_returns_unknown(self):
        df = pd.DataFrame({"track_name": ["Track A"]})
        result = detect_mood_archetype(df)
        assert result["archetype"] == "Unknown"


# ── calculate_audio_profile ────────────────────────────────────────────────────

class TestAudioProfile:
    def test_all_values_in_0_1(self, sample_tracks_df):
        profile = calculate_audio_profile(sample_tracks_df)
        for key, val in profile.items():
            if "normalized" in key or key in [
                "danceability", "energy", "valence",
                "acousticness", "speechiness", "instrumentalness", "liveness",
            ]:
                assert 0.0 <= val <= 1.0, f"{key}={val} out of [0,1]"

    def test_tempo_normalized_present(self, sample_tracks_df):
        sample_tracks_df["tempo"] = 120.0
        profile = calculate_audio_profile(sample_tracks_df)
        assert "tempo_normalized" in profile
        assert profile["tempo_normalized"] == pytest.approx(0.6, abs=0.01)
