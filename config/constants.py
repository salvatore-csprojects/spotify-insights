"""
config/constants.py
-------------------
All magic numbers, color maps, feature lists, and labels in one place.
Never import these at module level in hot paths — import the dict/list you need.
"""

# ── Spotify audio features returned by /audio-features ────────────────────────
AUDIO_FEATURES = [
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
    "time_signature",
]

# Features useful for user-facing analysis (subset, no key/mode/time_sig)
ANALYSIS_FEATURES = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]

# ── Popularity bucketing ───────────────────────────────────────────────────────
POPULARITY_BUCKETS = {
    "Underground (0–29)": (0, 29),
    "Indie (30–49)": (30, 49),
    "Mid-tier (50–69)": (50, 69),
    "Mainstream (70–89)": (70, 89),
    "Mega-hit (90–100)": (90, 100),
}

# ── Mood archetypes ────────────────────────────────────────────────────────────
# Defined by (valence_low, valence_high, energy_low, energy_high)
MOOD_ARCHETYPES = {
    "Euphoria Mode": {"valence": (0.6, 1.0), "energy": (0.6, 1.0)},
    "Dark Intensity": {"valence": (0.0, 0.4), "energy": (0.6, 1.0)},
    "Sunday Chill": {"valence": (0.6, 1.0), "energy": (0.0, 0.5)},
    "Introspective": {"valence": (0.0, 0.5), "energy": (0.0, 0.5)},
    "Balanced Flow": {"valence": (0.4, 0.6), "energy": (0.4, 0.6)},
}

# ── Streamlit / Plotly color palette (Spotify-inspired dark theme) ─────────────
COLORS = {
    "spotify_green": "#1DB954",
    "spotify_black": "#121212",
    "card_bg": "#181818",
    "card_bg_hover": "#282828",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B3B3B3",
    "text_muted": "#535353",
    "accent_1": "#1DB954",   # Spotify green
    "accent_2": "#FF6437",   # Warm orange for contrast
    "accent_3": "#509BF5",   # Cool blue
    "accent_4": "#C278E0",   # Purple
}

PLOTLY_TEMPLATE = "plotly_dark"

# Color sequence for multi-series charts
CHART_COLOR_SEQUENCE = [
    "#1DB954",  # Spotify green
    "#FF6437",  # Orange
    "#509BF5",  # Blue
    "#C278E0",  # Purple
    "#F59B23",  # Amber
    "#FF4081",  # Pink
]

# ── Time range display names ───────────────────────────────────────────────────
TIME_RANGE_LABELS = {
    "short_term": "Last 4 Weeks",
    "medium_term": "Last 6 Months",
    "long_term": "All Time",
}

# ── Diversity score labels ─────────────────────────────────────────────────────
DIVERSITY_BANDS = [
    (0.0, 0.2, "Echo Chamber", "🔁"),
    (0.2, 0.4, "Comfort Listener", "🎵"),
    (0.4, 0.6, "Selective Explorer", "🗺️"),
    (0.6, 0.8, "Eclectic Taste", "🎭"),
    (0.8, 1.0, "Genre Nomad", "🌍"),
]

# ── Insight copy templates ─────────────────────────────────────────────────────
# Use .format(**kwargs) or f-string interpolation
INSIGHT_TEMPLATES = {
    "top_artist_dominant": (
        "Your top artist {artist} accounts for {pct:.0f}% of your recent listening — "
        "you're clearly in a phase."
    ),
    "high_diversity": (
        "Your diversity score of {score:.2f} puts you in the top tier of explorers. "
        "You're pulling from {genre_count} distinct genres right now."
    ),
    "low_diversity": (
        "You're deep in a comfort zone — {top_genre} dominates {pct:.0f}% of your recent plays. "
        "Nothing wrong with that."
    ),
    "mainstream_listener": (
        "Your average popularity of {avg:.0f}/100 skews mainstream. "
        "You're tracking with what's hot right now."
    ),
    "underground_listener": (
        "With an average popularity of {avg:.0f}/100, you're finding music "
        "most people haven't heard yet."
    ),
    "high_energy": (
        "High energy ({avg:.0f}/100) dominates your listening. "
        "Your soundtrack is built for momentum."
    ),
    "high_valence": (
        "Your playlist skews positive — avg valence {avg:.0f}/100. "
        "You're reaching for music that lifts."
    ),
    "taste_drift": (
        "Your taste has shifted noticeably since last month. "
        "{new_artists} new artists appeared in your top 50."
    ),
}
