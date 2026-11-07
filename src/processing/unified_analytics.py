"""Orchestrate the developer-event processing modules into one analytics pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from .clean_developer_events import clean_developer_events
from .context_switch_analysis import analyze_context_switches
from .developer_metrics import calculate_developer_metrics
from .developer_sessions import detect_developer_sessions
from .flow_blocks import calculate_flow_summary, detect_flow_blocks
from .interruption_analysis import (
    calculate_interruption_summary,
    detect_potential_interruptions,
)
from .load_developer_events import process_event_file


def _ensure_utc_datetime(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return rows with parseable UTC timestamps and rows with bad timestamps."""
    if "event_timestamp" not in df.columns:
        raise ValueError("Input is missing required column: event_timestamp")

    dtype = df.schema["event_timestamp"]
    if isinstance(dtype, pl.Datetime):
        if dtype.time_zone is None:
            df = df.with_columns(
                pl.col("event_timestamp").dt.replace_time_zone("UTC")
            )
        elif dtype.time_zone != "UTC":
            df = df.with_columns(
                pl.col("event_timestamp").dt.convert_time_zone("UTC")
            )
        bad = df.filter(pl.col("event_timestamp").is_null())
        good = df.filter(pl.col("event_timestamp").is_not_null())
        return good, bad

    if dtype == pl.String:
        parsed = df.with_columns(
            pl.col("event_timestamp")
            .str.to_datetime(time_zone="UTC", strict=False)
            .alias("event_timestamp")
        )
        bad = parsed.filter(pl.col("event_timestamp").is_null())
        good = parsed.filter(pl.col("event_timestamp").is_not_null())
        return good, bad

    raise TypeError(
        "event_timestamp must be a Polars Datetime or String column"
    )


def _empty_rejected_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={"record": pl.String, "reason": pl.String}
    )


def run_unified_analytics(
    events_df: pl.DataFrame,
    *,
    idle_threshold_minutes: int = 30,
    max_flow_gap_minutes: int = 10,
    min_flow_block_minutes: int = 15,
    interruption_window_minutes: int = 5,
) -> dict[str, Any]:
    """
    Run cleaning, session, context-switch, flow-block, interruption,
    and developer-metric analysis.

    Returns a dictionary containing each intermediate DataFrame,
    the combined developer metrics, and data-quality reports.
    """
    if not isinstance(events_df, pl.DataFrame):
        raise TypeError("events_df must be a Polars DataFrame")

    if idle_threshold_minutes <= 0:
        raise ValueError("idle_threshold_minutes must be greater than zero")
    if max_flow_gap_minutes < 0 or min_flow_block_minutes < 0:
        raise ValueError("Flow thresholds cannot be negative")
    if interruption_window_minutes <= 0:
        raise ValueError("interruption_window_minutes must be greater than zero")

    cleaned_df, rejected_df, cleaning_report = clean_developer_events(events_df)
    timestamped_df, invalid_timestamp_df = _ensure_utc_datetime(cleaned_df)

    if not invalid_timestamp_df.is_empty():
        timestamp_rejections = invalid_timestamp_df.with_columns(
            pl.lit("Invalid event_timestamp after parsing").alias("rejection_reason")
        )
        rejected_df = pl.concat(
            [rejected_df, timestamp_rejections],
            how="diagonal_relaxed",
        )

    # All downstream analysis functions expect a UTC Datetime column.
    cleaned_df = timestamped_df.sort(["developer_id", "event_timestamp"])

    sessions_df, event_sessions_df = detect_developer_sessions(
        cleaned_df,
        idle_threshold_minutes=idle_threshold_minutes,
    )

    context_summary_df, transitions_df = analyze_context_switches(
        cleaned_df,
        idle_threshold_minutes=idle_threshold_minutes,
    )

    flow_blocks_df, event_blocks_df = detect_flow_blocks(
        cleaned_df,
        max_gap_minutes=max_flow_gap_minutes,
        min_block_minutes=min_flow_block_minutes,
    )
    flow_summary_df = calculate_flow_summary(flow_blocks_df)

    interruptions_df, coding_events_df = detect_potential_interruptions(
        cleaned_df,
        window_minutes=interruption_window_minutes,
    )
    interruption_summary_df = calculate_interruption_summary(
        interruptions_df,
        coding_events_df,
    )

    developer_metrics_df = calculate_developer_metrics(
        cleaned_df,
        sessions_df,
        transitions_df,
    )

    # Enrich the base developer metrics with the additional analysis summaries.
    for summary in (context_summary_df, flow_summary_df, interruption_summary_df):
        if "developer_id" in summary.columns and not summary.is_empty():
            extra_columns = [
                column for column in summary.columns
                if column != "developer_id"
                and column not in developer_metrics_df.columns
            ]
            if extra_columns:
                developer_metrics_df = developer_metrics_df.join(
                    summary.select(["developer_id", *extra_columns]),
                    on="developer_id",
                    how="left",
                )

    return {
        "cleaned_events": cleaned_df,
        "rejected_events": rejected_df,
        "sessions": sessions_df,
        "event_sessions": event_sessions_df,
        "context_switch_summary": context_summary_df,
        "context_switch_transitions": transitions_df,
        "flow_blocks": flow_blocks_df,
        "event_blocks": event_blocks_df,
        "flow_summary": flow_summary_df,
        "potential_interruptions": interruptions_df,
        "coding_events": coding_events_df,
        "interruption_summary": interruption_summary_df,
        "developer_metrics": developer_metrics_df,
        "quality_report": {
            **cleaning_report,
            "invalid_timestamp_records": invalid_timestamp_df.height,
            "final_accepted_records": cleaned_df.height,
            "final_rejected_records": rejected_df.height,
        },
    }


def run_unified_analytics_from_file(
    file_path: str | Path,
    *,
    idle_threshold_minutes: int = 30,
    max_flow_gap_minutes: int = 10,
    min_flow_block_minutes: int = 15,
    interruption_window_minutes: int = 5,
) -> dict[str, Any]:
    """Load a JSON event file and run the complete analytics pipeline."""
    loaded_df, load_rejected_df = process_event_file(file_path)

    results = run_unified_analytics(
        loaded_df,
        idle_threshold_minutes=idle_threshold_minutes,
        max_flow_gap_minutes=max_flow_gap_minutes,
        min_flow_block_minutes=min_flow_block_minutes,
        interruption_window_minutes=interruption_window_minutes,
    )

    results["load_rejected_events"] = load_rejected_df
    results["quality_report"]["load_rejected_records"] = load_rejected_df.height
    results["quality_report"]["total_rejected_records"] = (
        results["quality_report"]["final_rejected_records"]
        + load_rejected_df.height
    )
    return results
