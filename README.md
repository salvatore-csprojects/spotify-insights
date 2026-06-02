<div align="center">

<img src="assets/banner.png" alt="Spotify Insights Banner" width="100%"/>

# 🎵 Spotify Insights

### Personal Music Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Spotipy](https://img.shields.io/badge/Spotipy-2.23+-1DB954?style=flat-square&logo=spotify&logoColor=white)](https://spotipy.readthedocs.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?style=flat-square&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)

**Spotify Insights** is a full-stack personal analytics platform that transforms raw Spotify listening data into a premium, interactive intelligence dashboard — think Spotify Wrapped, but available 365 days a year, with deeper analytics you actually control.

[**Coming Soon — Streamlit Cloud**](#)

</div>

---

## 📸 Dashboard Preview
> Screenshots coming soon. Run locally with `streamlit run streamlit_app/app.py` to see the full dashboard.

---

## ✨ Features

### 🎯 Core Analytics
- **Multi-horizon listening profiles** — short (4 weeks), medium (6 months), long-term (all time) comparison
- **Listening Evolution Engine** — detects taste drift, emerging obsessions, and genre pivots over time
- **Artist Concentration Score** — quantifies how niche or mainstream your taste is (Herfindahl-Hirschman Index adapted for music)
- **Audio Feature Intelligence** — radar charts and scatter analysis across valence, energy, danceability, acousticness, speechiness, tempo

### 🧠 Automated Insights
- Rule-based narrative engine generating personalized, human-readable listening summaries
- **Mood Archetype Detection** — classifies your listening session into profiles (Night Driver, Gym Warrior, Sunday Chill, etc.)
- **Diversity Score** — entropy-based metric across genres, decades, and popularity tiers
- **Repeat Behavior Analysis** — surfaces whether you're a discovery-first or comfort-listening person

### 📊 Visualizations
- Spotify Wrapped–style animated summary cards
- Artist radar / spider charts for audio feature comparison
- Popularity vs. obscurity scatter plots with genre coloring
- Time-range evolution heatmaps
- Interactive drilldown: click any artist → see all their tracks in your top list

### 🔌 Data Engineering
- Modular ETL pipeline with configurable time ranges
- `@st.cache_data` + disk-based caching to minimize API calls
- Schema validation via Pydantic on all API responses
- Structured logging with rotation
- Rate-limit aware Spotify API client

---

## 🏗️ Architecture

```
spotify-insights/
│
├── src/
│   ├── api/
│   │   ├── client.py          # Authenticated Spotipy client with retry logic
│   │   ├── extract.py         # Top tracks, audio features, genres, recently played
│   │   └── schemas.py         # Pydantic models for API response validation
│   │
│   ├── processing/
│   │   ├── cleaning.py        # Dedup, type casting, null handling
│   │   ├── enrichment.py      # Genre inference, popularity bucketing, era tagging
│   │   └── validation.py      # Post-processing data quality checks
│   │
│   ├── analytics/
│   │   ├── kpis.py            # Core metric calculations
│   │   ├── insights.py        # Narrative engine — generates text insights
│   │   ├── audio_features.py  # Audio feature analysis and scoring
│   │   ├── evolution.py       # Taste drift detection across time ranges
│   │   └── diversity.py       # Entropy-based diversity scoring
│   │
│   └── utils/
│       ├── logger.py          # Structured logging setup
│       └── cache.py           # Disk + memory caching utilities
│
├── streamlit_app/
│   ├── app.py                 # Main entry point, page config, auth gate
│   ├── components/
│   │   ├── kpi_cards.py       # Premium metric card components
│   │   ├── charts.py          # All chart factory functions
│   │   └── insights_panel.py  # Narrative insight display
│   └── pages/
│       ├── 1_Overview.py      # KPI summary + Wrapped-style hero
│       ├── 2_Deep_Dive.py     # Artist + track drilldowns
│       ├── 3_Audio_Lab.py     # Audio feature analysis
│       ├── 4_Evolution.py     # Taste over time
│       └── 5_Discover.py      # Recommendations + hidden gems
│
├── config/
│   ├── settings.py            # Env-driven config (Pydantic BaseSettings)
│   └── constants.py           # Feature lists, thresholds, color maps
│
├── data/
│   ├── raw/                   # Unprocessed API responses (JSON + CSV)
│   └── processed/             # Cleaned, enriched, analysis-ready CSVs
│
├── tests/
│   ├── test_kpis.py
│   ├── test_insights.py
│   └── test_api_client.py
│
├── notebooks/
│   └── exploration.ipynb      # EDA and feature development notebook
│
├── .streamlit/
│   └── config.toml            # Theme: dark mode, Spotify color palette
│
├── main.py                    # CLI pipeline runner
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/salvatore-csprojects/spotify-insights.git
cd spotify-insights
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Spotify credentials

```bash
cp .env.example .env
```

Edit `.env`:
```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

> **Get credentials**: [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) → Create App → copy Client ID + Secret

### 3. Run the ETL pipeline

```bash
python main.py
```

This will:
- Authenticate via OAuth2 PKCE
- Extract top tracks (all 3 time ranges) + audio features + recently played
- Clean, enrich, and save to `data/processed/`
- Output a pipeline summary with record counts and data quality metrics

### 4. Launch the dashboard

```bash
streamlit run streamlit_app/app.py
```

---

## 📐 Analytics Methodology

### Diversity Score
Adapted Shannon Entropy across three dimensions:
```python
H = -Σ p(x) * log2(p(x))
# Normalized across: genre distribution, popularity tiers (0-100 → 5 buckets), release decade
diversity_score = (H_genre + H_popularity + H_decade) / 3
```

### Artist Concentration Index
Herfindahl-Hirschman Index adapted for listening share:
```python
HHI = Σ (artist_track_share)²
# 0.0 = perfectly distributed, 1.0 = single-artist monopoly
concentration = HHI  # lower = more eclectic
```

### Mood Archetype
K-means clustering on normalized audio features [valence, energy, danceability, acousticness]:
```
High valence + high energy  → "Euphoria Mode"
Low valence + high energy   → "Dark Intensity"
High valence + low energy   → "Sunday Chill"
Low valence + low energy    → "Introspective"
```

---

## 🧪 Testing

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## 🌐 Deployment

### Streamlit Cloud (recommended for portfolio)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, set `streamlit_app/app.py` as entry point
4. Add secrets in the Streamlit Cloud dashboard (same keys as `.env`)

### Docker

```bash
docker build -t spotify-insights .
docker run -p 8501:8501 --env-file .env spotify-insights
```

---

## 📊 Sample Metrics (from real data)

| Metric | Value |
|--------|-------|
| API endpoints used | 7 |
| Max tracks analyzed | 150 (50 × 3 ranges) |
| Audio features per track | 13 |
| Automated insights generated | 12–18 per session |
| Dashboard pages | 5 |
| Chart types | 11 |

---

## 🛣️ Roadmap

- [ ] Last.fm scrobble integration for true historical data
- [ ] Friend comparison mode (OAuth multi-user)
- [ ] Playlist health score + auto-optimization
- [ ] Genre evolution timeline (alluvial chart)
- [ ] Export to PDF — personal Wrapped report
- [ ] Scheduled daily ETL via GitHub Actions

---

## 🤝 Contributing

PRs welcome. Please open an issue first for major changes. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

<div align="center">

Built with 🎧 by [Salvatore](https://github.com/salvatore-csprojects) · Not affiliated with Spotify AB

</div>
