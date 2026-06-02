"""
streamlit_app/app.py
--------------------
Entry point. Handles:
  - Page config + theme injection
  - Auth gate (shows connect button if data not loaded)
  - Sidebar navigation
  - Cross-page state management via st.session_state
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import streamlit as st

# ── Page config MUST be first Streamlit call ───────────────────────────────────
st.set_page_config(
    page_title="Spotify Insights",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/yourname/spotify-insights",
        "Report a bug": "https://github.com/yourname/spotify-insights/issues",
        "About": "Personal music intelligence platform. Not affiliated with Spotify AB.",
    },
)

# ── Custom CSS: premium dark SaaS look ────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Global typography ────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Hide default Streamlit chrome ────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d0d0d;
    border-right: 1px solid #1a1a1a;
}
[data-testid="stSidebar"] * {
    color: #b3b3b3 !important;
}
[data-testid="stSidebar"] .stSelectbox label {
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #535353 !important;
}

/* ── KPI cards ────────────────────────────────────────── */
.kpi-card {
    background: #181818;
    border: 1px solid #282828;
    border-radius: 12px;
    padding: 20px 24px;
    transition: border-color 0.2s;
}
.kpi-card:hover {
    border-color: #1DB954;
}
.kpi-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #535353;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 32px;
    font-weight: 600;
    color: #ffffff;
    line-height: 1;
}
.kpi-sub {
    font-size: 12px;
    color: #535353;
    margin-top: 6px;
}

/* ── Insight cards ────────────────────────────────────── */
.insight-card {
    background: #181818;
    border-left: 3px solid #1DB954;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.insight-category {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #535353;
    margin-bottom: 6px;
}
.insight-text {
    font-size: 14px;
    color: #e0e0e0;
    line-height: 1.5;
}

/* ── Section headers ──────────────────────────────────── */
.section-header {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #535353;
    padding-bottom: 12px;
    border-bottom: 1px solid #1a1a1a;
    margin-bottom: 24px;
}

/* ── Wrapped hero ─────────────────────────────────────── */
.wrapped-hero {
    background: linear-gradient(135deg, #1DB954 0%, #0d7a36 50%, #121212 100%);
    border-radius: 16px;
    padding: 40px 48px;
    margin-bottom: 32px;
}
.wrapped-title {
    font-size: 42px;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.1;
}
.wrapped-subtitle {
    font-size: 16px;
    color: rgba(255,255,255,0.7);
    margin-top: 8px;
}

/* ── Charts ────────────────────────────────────────────── */
.element-container iframe {
    border-radius: 12px;
}

/* ── Table styling ─────────────────────────────────────── */
.dataframe {
    background: #181818 !important;
    border: none !important;
    font-size: 13px;
}
.dataframe th {
    background: #121212 !important;
    color: #535353 !important;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-bottom: 1px solid #282828 !important;
}
.dataframe td {
    color: #b3b3b3 !important;
    border-color: #1a1a1a !important;
}

/* ── Tabs ──────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 1px solid #282828;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #535353;
    font-size: 13px;
    font-weight: 500;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    background: transparent;
    color: #ffffff;
    border-bottom: 2px solid #1DB954;
}

/* ── Metrics override ─────────────────────────────────── */
[data-testid="stMetricValue"] {
    font-size: 28px;
    color: #ffffff;
}
[data-testid="stMetricLabel"] {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #535353;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Data loading ───────────────────────────────────────────────────────────────
import os
import pandas as pd


@st.cache_data(ttl=3600, show_spinner=False)
def load_processed_data(time_range: str) -> pd.DataFrame:
    """Load processed CSV for a given time range. Returns empty DF if not found."""
    path = f"data/processed/top_tracks_{time_range}_cleaned.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Failed to load data for {time_range}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_artists_data(time_range: str) -> pd.DataFrame:
    path = f"data/processed/top_artists_{time_range}_cleaned.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_recently_played() -> pd.DataFrame:
    path = "data/processed/recently_played_cleaned.csv"
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 16px 0 24px;">
            <div style="font-size: 20px; font-weight: 700; color: #1DB954; letter-spacing: -0.5px;">
                ◈ Spotify Insights
            </div>
            <div style="font-size: 11px; color: #535353; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.1em;">
                Music Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-header">Time Range</div>', unsafe_allow_html=True
    )

    time_range = st.selectbox(
        "Time range",
        options=["short_term", "medium_term", "long_term"],
        format_func=lambda x: {
            "short_term": "Last 4 Weeks",
            "medium_term": "Last 6 Months",
            "long_term": "All Time",
        }[x],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown(
        '<div class="section-header">Actions</div>', unsafe_allow_html=True
    )

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("📊 Run ETL Pipeline", use_container_width=True):
        with st.spinner("Running pipeline..."):
            import subprocess
            result = subprocess.run(
                ["python", "main.py"], capture_output=True, text=True, cwd=project_root
            )
            if result.returncode == 0:
                st.success("Pipeline complete")
                st.cache_data.clear()
            else:
                st.error(f"Pipeline failed:\n{result.stderr}")

    st.markdown("---")
    st.markdown(
        '<div style="font-size:11px; color:#535353;">Not affiliated with Spotify AB</div>',
        unsafe_allow_html=True,
    )

# ── Session state ──────────────────────────────────────────────────────────────
if "time_range" not in st.session_state:
    st.session_state.time_range = time_range
else:
    st.session_state.time_range = time_range

# ── Load data ──────────────────────────────────────────────────────────────────
with st.spinner("Loading your music data..."):
    df = load_processed_data(time_range)
    artists_df = load_artists_data(time_range)
    recently_played_df = load_recently_played()

# ── Data gate ──────────────────────────────────────────────────────────────────
if df.empty:
    st.markdown(
        f"""
        <div class="wrapped-hero">
            <div class="wrapped-title">Your data isn't loaded yet.</div>
            <div class="wrapped-subtitle">
                Run the ETL pipeline from the sidebar, or use the CLI: <code>python main.py</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "**First-time setup:** The pipeline will open a Spotify OAuth window in your browser. "
        "Authenticate once — credentials are cached locally.",
        icon="ℹ️",
    )
    st.stop()

# ── Main dashboard ─────────────────────────────────────────────────────────────
# Import analytics
from src.analytics.kpis import (
    calculate_track_kpis,
    calculate_diversity_score,
    calculate_concentration_index,
    detect_mood_archetype,
    calculate_audio_profile,
)
from src.analytics.insights import generate_insights
from config.constants import TIME_RANGE_LABELS

kpis = calculate_track_kpis(df)
diversity = calculate_diversity_score(df, artists_df if not artists_df.empty else None)
concentration = calculate_concentration_index(df)
mood = detect_mood_archetype(df)

# ── Wrapped Hero ───────────────────────────────────────────────────────────────
time_label = TIME_RANGE_LABELS.get(time_range, time_range)
top_artist = df["artist"].value_counts().index[0] if not df.empty and "artist" in df.columns else "—"
top_track = df.iloc[0]["track_name"] if not df.empty and "track_name" in df.columns else "—"

st.markdown(
    f"""
    <div class="wrapped-hero">
        <div class="wrapped-title">Your Sound — {time_label}</div>
        <div class="wrapped-subtitle">
            Top artist: <strong>{top_artist}</strong> · Mood: <strong>{mood.get('archetype', '—')}</strong> · {diversity.get('emoji', '')} {diversity.get('label', '')}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── KPI Row 1 ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

def kpi_card(col, label: str, value: str, sub: str = "") -> None:
    col.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {"<div class='kpi-sub'>" + sub + "</div>" if sub else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

kpi_card(col1, "Tracks Analyzed", str(kpis.get("total_tracks", 0)))
kpi_card(col2, "Unique Artists", str(kpis.get("unique_artists", 0)))
kpi_card(col3, "Avg Popularity", f"{kpis.get('avg_popularity', 0):.0f}", "out of 100")
kpi_card(col4, "Diversity Score", f"{diversity.get('score', 0):.2f}", diversity.get("label", ""))
kpi_card(col5, "Mood", mood.get("archetype", "—"), f"v:{mood.get('avg_valence',0):.2f} e:{mood.get('avg_energy',0):.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["🎧 Overview", "🎨 Audio Lab", "📈 Evolution", "✨ Insights"]
)

# ============================================================
# TAB 1: OVERVIEW
# ============================================================
with tab1:
    import plotly.express as px
    import plotly.graph_objects as go
    from config.constants import CHART_COLOR_SEQUENCE, PLOTLY_TEMPLATE

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        st.markdown('<div class="section-header">Top Artists</div>', unsafe_allow_html=True)
        if "artist" in df.columns:
            top_artists = df["artist"].value_counts().head(12).reset_index()
            top_artists.columns = ["artist", "track_count"]
            fig = px.bar(
                top_artists,
                x="track_count",
                y="artist",
                orientation="h",
                color="track_count",
                color_continuous_scale=["#1a1a1a", "#1DB954"],
                template=PLOTLY_TEMPLATE,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                yaxis=dict(categoryorder="total ascending"),
                margin=dict(l=0, r=0, t=0, b=0),
                height=380,
                font=dict(color="#b3b3b3", size=12),
                xaxis=dict(gridcolor="#1a1a1a", title=""),
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<div class="section-header">Popularity Tiers</div>', unsafe_allow_html=True)
        pop_dist = kpis.get("popularity_distribution", {})
        if pop_dist:
            fig2 = go.Figure(
                go.Pie(
                    labels=list(pop_dist.keys()),
                    values=list(pop_dist.values()),
                    hole=0.55,
                    marker_colors=["#1DB954", "#17963e", "#0e6b2c", "#0a4d1f", "#062e12"],
                    textinfo="percent",
                    textfont_size=11,
                )
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    font=dict(color="#b3b3b3", size=11),
                    bgcolor="rgba(0,0,0,0)",
                    x=0,
                ),
                margin=dict(l=0, r=0, t=0, b=0),
                height=380,
                font=dict(color="#b3b3b3"),
                annotations=[
                    dict(
                        text=f"avg<br><b style='font-size:18px'>{kpis.get('avg_popularity', 0):.0f}</b>",
                        x=0.5, y=0.5,
                        font_size=12,
                        showarrow=False,
                        font_color="#ffffff",
                    )
                ],
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Popularity vs Energy scatter ──────────────────────────────────────
    st.markdown('<div class="section-header">Popularity × Energy Landscape</div>', unsafe_allow_html=True)
    if "popularity" in df.columns and "energy" in df.columns:
        scatter_df = df.copy()
        if "danceability" in scatter_df.columns:
            scatter_df["marker_size"] = scatter_df["danceability"] * 20 + 5
        else:
            scatter_df["marker_size"] = 10

        hover_cols = ["track_name", "artist", "popularity"]
        if "valence" in scatter_df.columns:
            hover_cols.append("valence")

        fig3 = px.scatter(
            scatter_df,
            x="popularity",
            y="energy",
            size="marker_size",
            color="artist",
            hover_data=hover_cols,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=CHART_COLOR_SEQUENCE,
            opacity=0.8,
        )
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            showlegend=False,
            xaxis=dict(gridcolor="#1a1a1a", title="Popularity →"),
            yaxis=dict(gridcolor="#1a1a1a", title="Energy →"),
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(color="#b3b3b3", size=12),
        )
        # Quadrant labels
        fig3.add_annotation(x=85, y=0.92, text="Mainstream Bangers", showarrow=False,
                            font=dict(size=10, color="#535353"))
        fig3.add_annotation(x=15, y=0.92, text="Underground Intensity", showarrow=False,
                            font=dict(size=10, color="#535353"))
        fig3.add_annotation(x=85, y=0.08, text="Popular & Chill", showarrow=False,
                            font=dict(size=10, color="#535353"))
        fig3.add_annotation(x=15, y=0.08, text="Hidden Gems", showarrow=False,
                            font=dict(size=10, color="#535353"))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── Track table ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Track Rankings</div>', unsafe_allow_html=True)
    display_cols = ["rank", "track_name", "artist", "popularity"]
    audio_display = ["danceability", "energy", "valence"]
    for c in audio_display:
        if c in df.columns:
            display_cols.append(c)

    display_df = df[[c for c in display_cols if c in df.columns]].copy()
    for c in audio_display:
        if c in display_df.columns:
            display_df[c] = (display_df[c] * 100).round(0).astype("Int64").astype(str) + "%"

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=420,
    )

# ============================================================
# TAB 2: AUDIO LAB
# ============================================================
with tab2:
    from src.analytics.kpis import calculate_audio_profile
    import plotly.graph_objects as go

    audio_profile = calculate_audio_profile(df)

    st.markdown('<div class="section-header">Audio Feature Radar</div>', unsafe_allow_html=True)

    radar_features = ["danceability", "energy", "valence", "acousticness",
                      "speechiness", "instrumentalness", "liveness"]
    radar_vals = [audio_profile.get(f, 0) for f in radar_features]
    radar_vals_closed = radar_vals + [radar_vals[0]]
    radar_labels = [f.capitalize() for f in radar_features] + [radar_features[0].capitalize()]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_vals_closed,
        theta=radar_labels,
        fill="toself",
        fillcolor="rgba(29, 185, 84, 0.15)",
        line=dict(color="#1DB954", width=2),
        name=time_label,
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 1],
                gridcolor="#282828", color="#535353",
                tickfont=dict(size=10, color="#535353"),
            ),
            angularaxis=dict(gridcolor="#282828", color="#535353"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b3b3b3"),
        height=450,
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
    )
    col_r1, col_r2, col_r3 = st.columns([1.5, 1, 1])
    with col_r1:
        st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

    with col_r2:
        st.markdown('<div class="section-header">Feature Breakdown</div>', unsafe_allow_html=True)
        for feat in radar_features:
            val = audio_profile.get(feat, 0)
            st.markdown(
                f"""
                <div style="margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; font-size:12px; color:#b3b3b3; margin-bottom:4px;">
                        <span>{feat.capitalize()}</span>
                        <span style="color:#1DB954;">{val:.2f}</span>
                    </div>
                    <div style="height:4px; background:#1a1a1a; border-radius:2px;">
                        <div style="width:{val*100:.0f}%; height:4px; background:#1DB954; border-radius:2px;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_r3:
        st.markdown('<div class="section-header">Mood Archetype</div>', unsafe_allow_html=True)
        arch = mood.get("archetype", "—")
        arch_emojis = {
            "Euphoria Mode": "🔥",
            "Dark Intensity": "🌑",
            "Sunday Chill": "☀️",
            "Introspective": "🌧️",
            "Balanced Flow": "⚖️",
        }
        st.markdown(
            f"""
            <div class="kpi-card" style="text-align:center; padding:32px 16px;">
                <div style="font-size:48px; margin-bottom:12px;">{arch_emojis.get(arch, "🎵")}</div>
                <div style="font-size:20px; font-weight:600; color:#ffffff; margin-bottom:8px;">{arch}</div>
                <div style="font-size:12px; color:#535353;">
                    Valence {mood.get('avg_valence', 0):.2f} · Energy {mood.get('avg_energy', 0):.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Feature distribution histograms ───────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Feature Distributions</div>', unsafe_allow_html=True)
    hist_features = ["valence", "energy", "danceability", "acousticness"]
    hist_cols = st.columns(4)
    for i, feat in enumerate(hist_features):
        if feat in df.columns:
            with hist_cols[i]:
                fig_h = px.histogram(
                    df, x=feat, nbins=20,
                    template=PLOTLY_TEMPLATE,
                    color_discrete_sequence=["#1DB954"],
                    title=feat.capitalize(),
                )
                fig_h.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=180,
                    showlegend=False,
                    margin=dict(l=0, r=0, t=30, b=0),
                    font=dict(color="#b3b3b3", size=10),
                    xaxis=dict(gridcolor="#1a1a1a", title=""),
                    yaxis=dict(gridcolor="#1a1a1a", title="", visible=False),
                    title_font_size=12,
                )
                st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

# ============================================================
# TAB 3: EVOLUTION
# ============================================================
with tab3:
    from src.analytics.evolution import compare_time_ranges, build_rank_evolution_df

    st.markdown('<div class="section-header">Taste Evolution Across Time Ranges</div>', unsafe_allow_html=True)

    # Load all 3 ranges for comparison
    all_dfs = {
        "short_term": load_processed_data("short_term"),
        "medium_term": load_processed_data("medium_term"),
        "long_term": load_processed_data("long_term"),
    }

    evolution_data = compare_time_ranges({k: v for k, v in all_dfs.items() if not v.empty})

    if "error" not in evolution_data:
        # ── Feature drift line chart ───────────────────────────────────────
        drift = evolution_data.get("feature_drift", {})
        if drift:
            drift_records = []
            for feat, values in drift.items():
                for t, val in values.items():
                    drift_records.append({"time_range": t, "feature": feat.capitalize(), "value": val})
            drift_df = pd.DataFrame(drift_records)
            drift_df["time_label"] = drift_df["time_range"].map(TIME_RANGE_LABELS)

            features_to_plot = ["Popularity", "Energy", "Valence", "Danceability"]
            plot_drift = drift_df[drift_df["feature"].isin(features_to_plot)]

            if not plot_drift.empty:
                fig_drift = px.line(
                    plot_drift,
                    x="time_label",
                    y="value",
                    color="feature",
                    markers=True,
                    template=PLOTLY_TEMPLATE,
                    color_discrete_sequence=CHART_COLOR_SEQUENCE,
                )
                fig_drift.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=320,
                    legend=dict(
                        font=dict(color="#b3b3b3", size=11),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    xaxis=dict(gridcolor="#1a1a1a", title=""),
                    yaxis=dict(gridcolor="#1a1a1a", title="Normalized value (0–1)"),
                    font=dict(color="#b3b3b3", size=12),
                    margin=dict(l=0, r=0, t=0, b=0),
                )
                st.plotly_chart(fig_drift, use_container_width=True, config={"displayModeBar": False})

        # ── Artist emergence / fading ──────────────────────────────────────
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.markdown('<div class="section-header">Emerging Artists</div>', unsafe_allow_html=True)
            emerging = evolution_data.get("emerging_artists", [])
            if emerging:
                for a in emerging[:8]:
                    st.markdown(
                        f'<div style="font-size:13px; color:#1DB954; padding:4px 0; border-bottom:1px solid #1a1a1a;">↑ {a}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No new artists detected")

        with col_e2:
            st.markdown('<div class="section-header">Consistent Artists</div>', unsafe_allow_html=True)
            consistent = evolution_data.get("consistent_artists", [])
            if consistent:
                for a in consistent[:8]:
                    st.markdown(
                        f'<div style="font-size:13px; color:#b3b3b3; padding:4px 0; border-bottom:1px solid #1a1a1a;">→ {a}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No consistent artists found")

        with col_e3:
            st.markdown('<div class="section-header">Fading Artists</div>', unsafe_allow_html=True)
            fading = evolution_data.get("fading_artists", [])
            if fading:
                for a in fading[:8]:
                    st.markdown(
                        f'<div style="font-size:13px; color:#535353; padding:4px 0; border-bottom:1px solid #1a1a1a;">↓ {a}</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No fading artists detected")

        # ── Drift summary text ─────────────────────────────────────────────
        drift_summary = evolution_data.get("drift_summary", [])
        if drift_summary:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Signal Summary</div>', unsafe_allow_html=True)
            for signal in drift_summary:
                st.markdown(
                    f'<div class="insight-card"><div class="insight-text">📊 {signal}</div></div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("Load data for at least 2 time ranges to see evolution analysis.")

# ============================================================
# TAB 4: INSIGHTS
# ============================================================
with tab4:
    st.markdown('<div class="section-header">Personalized Insights</div>', unsafe_allow_html=True)

    insights = generate_insights(
        df,
        artists_df=artists_df if not artists_df.empty else None,
        top_n=8,
    )

    if insights:
        for insight in insights:
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-category">{insight['category']}</div>
                    <div class="insight-text">{insight['text']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No insights available — try running the ETL pipeline first.")

    # ── Concentration / diversity summary ─────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">Your Listening DNA</div>', unsafe_allow_html=True)

    dna_col1, dna_col2 = st.columns(2)
    with dna_col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Artist Concentration (HHI)</div>
                <div class="kpi-value">{concentration.get('hhi', 0):.3f}</div>
                <div class="kpi-sub">{concentration.get('label', '')} · {concentration.get('top_artist', '')} leads at {concentration.get('top_artist_share_pct', 0):.0f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with dna_col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Diversity Score</div>
                <div class="kpi-value">{diversity.get('emoji', '')} {diversity.get('score', 0):.2f}</div>
                <div class="kpi-sub">{diversity.get('label', '')} · Genre: {diversity.get('genre_entropy') or 'N/A'} · Pop tier: {diversity.get('popularity_entropy') or 'N/A'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
