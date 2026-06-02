"""
tests/test_cleaning.py
-----------------------
Unit tests for processing/cleaning.py.
"""

import pandas as pd
import pytest

from src.processing.cleaning import clean_tracks_data, clean_artists_data


@pytest.fixture
def raw_tracks():
    return pd.DataFrame(
        {
            "rank": [1, 2, 2, 3],   # rank 2 is a duplicate
            "track_id": ["t1", "t2", "t2", "t3"],
            "track_name": ["Song A", "Song B", "Song B (dup)", "Song C"],
            "artist": ["Artist X", "Artist Y", "Artist Y", "Artist Z"],
            "album": ["Album 1", "Album 2", "Album 2", "Album 3"],
            "release_date": ["2023-01-15", "2019-07-04", "2019-07-04", "1995-11-01"],
            "popularity": ["85", "105", "40", "-5"],  # intentionally messy types/values
            "duration_ms": [210_000, 180_000, 180_000, 240_000],
            "explicit": [1, 0, 0, 1],
            "danceability": [0.75, 1.2, 0.5, 0.3],   # 1.2 should be clipped to 1.0
            "energy": [0.8, 0.6, 0.55, 0.4],
            "valence": [0.6, 0.4, 0.4, 0.2],
            "acousticness": [-0.1, 0.3, 0.3, 0.7],  # -0.1 should be clipped to 0.0
            "speechiness": [0.05, 0.1, 0.1, 0.03],
            "instrumentalness": [0.0, 0.5, 0.5, 0.9],
            "liveness": [0.15, 0.12, 0.12, 0.2],
        }
    )


class TestCleanTracksData:
    def test_deduplicates_on_track_id(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert len(clean) == 3  # t1, t2, t3

    def test_popularity_clipped_to_100(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert clean["popularity"].max() <= 100

    def test_popularity_clipped_to_0(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert clean["popularity"].min() >= 0

    def test_danceability_clipped(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert clean["danceability"].max() <= 1.0

    def test_acousticness_clipped(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert clean["acousticness"].min() >= 0.0

    def test_duration_min_computed(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert "duration_min" in clean.columns
        # 210_000 ms = 3.5 min
        assert clean.loc[clean["track_id"] == "t1", "duration_min"].iloc[0] == pytest.approx(3.5, abs=0.01)

    def test_release_year_extracted(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert "release_year" in clean.columns
        t1_year = clean.loc[clean["track_id"] == "t1", "release_year"].iloc[0]
        assert int(t1_year) == 2023

    def test_era_tagged(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert "era" in clean.columns
        t3_era = clean.loc[clean["track_id"] == "t3", "era"].iloc[0]
        assert t3_era == "1990s"

    def test_popularity_category_assigned(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert "popularity_category" in clean.columns
        t1_cat = clean.loc[clean["track_id"] == "t1", "popularity_category"].iloc[0]
        assert "Mainstream" in t1_cat or "Mega" in t1_cat

    def test_empty_df_returns_empty(self):
        result = clean_tracks_data(pd.DataFrame())
        assert result.empty

    def test_index_reset(self, raw_tracks):
        clean = clean_tracks_data(raw_tracks)
        assert list(clean.index) == list(range(len(clean)))


class TestCleanArtistsData:
    def test_primary_genre_extracted(self):
        df = pd.DataFrame(
            {
                "artist_id": ["a1", "a2"],
                "artist_name": ["Artist A", "Artist B"],
                "genres": ["pop, dance pop, electropop", "hip hop, rap, trap"],
                "popularity": [80, 65],
                "followers": [1_000_000, 500_000],
            }
        )
        clean = clean_artists_data(df)
        assert "primary_genre" in clean.columns
        assert clean.loc[0, "primary_genre"] == "pop"
        assert clean.loc[1, "primary_genre"] == "hip hop"

    def test_followers_formatted(self):
        df = pd.DataFrame(
            {
                "artist_id": ["a1"],
                "artist_name": ["Artist"],
                "genres": ["pop"],
                "popularity": [70],
                "followers": [2_500_000],
            }
        )
        clean = clean_artists_data(df)
        assert "followers_fmt" in clean.columns
        assert clean.loc[0, "followers_fmt"] == "2.5M"
