"""
main.py
-------
CLI ETL pipeline orchestrator.

Usage:
    python main.py                  # Run full pipeline (all time ranges)
    python main.py --range short    # Single range
    python main.py --dry-run        # Validate auth without writing data
    python main.py --no-artists     # Skip artist extraction (faster)

Outputs:
    data/raw/          — raw JSON/CSV from Spotify API
    data/processed/    — cleaned, enriched, analysis-ready CSVs
    logs/pipeline.log  — structured run log with record counts
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Logging setup ──────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "pipeline.log", mode="a"),
    ],
)
logger = logging.getLogger("pipeline")

# ── Project root on sys.path ───────────────────────────────────────────────────
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.api.extract import (
    extract_top_tracks,
    extract_top_artists,
    extract_recently_played,
    extract_user_profile,
    save_dataframe,
)
from src.processing.cleaning import clean_tracks_data, clean_artists_data, clean_recently_played


def run_pipeline(
    time_ranges: list[str] | None = None,
    include_artists: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Full ETL pipeline. Returns a summary dict.
    """
    if time_ranges is None:
        time_ranges = settings.time_ranges

    start_ts = datetime.now(timezone.utc)
    summary = {
        "started_at": start_ts.isoformat(),
        "time_ranges": time_ranges,
        "records": {},
        "errors": [],
    }

    logger.info("=" * 60)
    logger.info("Spotify Insights — ETL Pipeline")
    logger.info("Time ranges: %s", time_ranges)
    logger.info("Dry run: %s", dry_run)
    logger.info("=" * 60)

    # ── User profile ───────────────────────────────────────────────────────
    try:
        profile = extract_user_profile()
        logger.info(
            "Authenticated as: %s (%s)",
            profile.get("display_name"),
            profile.get("product", "unknown tier"),
        )
    except Exception as e:
        logger.error("Auth failed: %s", e)
        summary["errors"].append(f"Auth: {e}")
        return summary

    if dry_run:
        logger.info("Dry run complete. Auth succeeded.")
        return summary

    # ── Tracks ────────────────────────────────────────────────────────────
    for time_range in time_ranges:
        logger.info("─── %s ────────────────────────────────────", time_range)

        try:
            # Extract
            t0 = time.perf_counter()
            raw_df = extract_top_tracks(time_range=time_range)
            elapsed = time.perf_counter() - t0

            if raw_df.empty:
                logger.warning("No tracks for %s — skipping", time_range)
                continue

            logger.info(
                "Extracted %d tracks in %.1fs (%.0f%% with audio features)",
                len(raw_df),
                elapsed,
                raw_df["danceability"].notna().mean() * 100
                if "danceability" in raw_df.columns
                else 0,
            )

            # Save raw
            raw_path = f"{settings.data_raw_dir}/top_tracks_{time_range}.csv"
            save_dataframe(raw_df, raw_path)

            # Clean + enrich
            clean_df = clean_tracks_data(raw_df)

            # Save processed
            processed_path = f"{settings.data_processed_dir}/top_tracks_{time_range}_cleaned.csv"
            save_dataframe(clean_df, processed_path)

            summary["records"][f"tracks_{time_range}"] = len(clean_df)

        except Exception as e:
            logger.error("Failed for %s: %s", time_range, e, exc_info=True)
            summary["errors"].append(f"tracks/{time_range}: {e}")

    # ── Artists ────────────────────────────────────────────────────────────
    if include_artists:
        for time_range in time_ranges:
            try:
                raw_artists = extract_top_artists(time_range=time_range)
                if raw_artists.empty:
                    continue

                save_dataframe(
                    raw_artists,
                    f"{settings.data_raw_dir}/top_artists_{time_range}.csv",
                )
                clean_artists = clean_artists_data(raw_artists)
                save_dataframe(
                    clean_artists,
                    f"{settings.data_processed_dir}/top_artists_{time_range}_cleaned.csv",
                )
                summary["records"][f"artists_{time_range}"] = len(clean_artists)

            except Exception as e:
                logger.error("Artist extraction failed for %s: %s", time_range, e)
                summary["errors"].append(f"artists/{time_range}: {e}")

    # ── Recently played ────────────────────────────────────────────────────
    try:
        raw_recent = extract_recently_played()
        if not raw_recent.empty:
            save_dataframe(
                raw_recent,
                f"{settings.data_raw_dir}/recently_played.csv",
            )
            clean_recent = clean_recently_played(raw_recent)
            save_dataframe(
                clean_recent,
                f"{settings.data_processed_dir}/recently_played_cleaned.csv",
            )
            summary["records"]["recently_played"] = len(clean_recent)
    except Exception as e:
        logger.warning("Recently played extraction failed: %s", e)
        summary["errors"].append(f"recently_played: {e}")

    # ── Summary ────────────────────────────────────────────────────────────
    elapsed_total = (datetime.now(timezone.utc) - start_ts).total_seconds()
    summary["duration_seconds"] = round(elapsed_total, 1)

    logger.info("=" * 60)
    logger.info("Pipeline complete in %.1fs", elapsed_total)
    for key, count in summary["records"].items():
        logger.info("  %-35s %d rows", key, count)
    if summary["errors"]:
        logger.warning("Errors encountered: %d", len(summary["errors"]))
        for err in summary["errors"]:
            logger.warning("  %s", err)
    logger.info("=" * 60)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spotify Insights — ETL pipeline")
    parser.add_argument(
        "--range",
        choices=["short", "medium", "long", "all"],
        default="all",
        help="Which time range(s) to run",
    )
    parser.add_argument(
        "--no-artists",
        action="store_true",
        help="Skip artist extraction",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate auth without writing data",
    )
    args = parser.parse_args()

    range_map = {
        "short": ["short_term"],
        "medium": ["medium_term"],
        "long": ["long_term"],
        "all": ["short_term", "medium_term", "long_term"],
    }

    result = run_pipeline(
        time_ranges=range_map[args.range],
        include_artists=not args.no_artists,
        dry_run=args.dry_run,
    )

    if result["errors"]:
        sys.exit(1)
