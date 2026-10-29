"""End-to-end processing and ClickHouse export for CogniStream."""

import logging
from datetime import date, datetime

import polars as pl

from src.database.clickhouse_client import (
    create_clickhouse_client,
    insert_developer_analytics,
)
from src.processing.activity_blocks import detect_activity_blocks
from src.processing.clickhouse_export import prepare_clickhouse_records
from src.processing.context_switching import analyze_context_switches
from src.processing.developer_metrics import calculate_developer_metrics
from src.processing.transform_events import transform_events
from src.processing.unified_analytics import build_unified_analytics


logger = logging.getLogger(__name__)


def build_analytics_records(
    events: list[dict],
    snapshot_date: date | str,
    inactivity_threshold_minutes: int = 15,
) -> list[dict]:
    """Transform developer events and prepare analytics records.

    This function prepares records without connecting to ClickHouse.
    """

    if not isinstance(events, list):
        raise TypeError("events must be a list of dictionaries.")

    if not all(isinstance(event, dict) for event in events):
        raise ValueError("Every event must be a dictionary.")

    if not isinstance(inactivity_threshold_minutes, int):
        raise TypeError("inactivity_threshold_minutes must be an integer.")

    if isinstance(inactivity_threshold_minutes, bool):
        raise TypeError("inactivity_threshold_minutes must be an integer.")

    if inactivity_threshold_minutes < 0:
        raise ValueError("inactivity_threshold_minutes cannot be negative.")

    if not events:
        logger.info("No events supplied; no analytics records generated.")
        return []

    logger.info("Starting analytics processing for %s events.", len(events))

    # Step 1: Convert event dictionaries into a Polars DataFrame.
    events_df = transform_events(events)

    if not isinstance(events_df, pl.DataFrame):
        raise TypeError("transform_events must return a Polars DataFrame.")

    if events_df.is_empty():
        logger.info("No transformed events available.")
        return []

    # Step 2: Calculate developer activity metrics.
    activity_metrics = calculate_developer_metrics(events_df)

    # Step 3: Calculate observable source/context transitions.
    context_metrics = analyze_context_switches(events_df)

    # Step 4: Group events into activity blocks.
    activity_blocks = detect_activity_blocks(
        events_df,
        inactivity_threshold_minutes=inactivity_threshold_minutes,
    )

    # Step 5: Combine the analytics datasets.
    unified_df = build_unified_analytics(
        activity_metrics,
        context_metrics,
        activity_blocks,
    )

    if not isinstance(unified_df, pl.DataFrame):
        raise TypeError(
            "build_unified_analytics must return a Polars DataFrame."
        )

    # Step 6: Prepare database-ready records.
    records = prepare_clickhouse_records(
        unified_df,
        snapshot_date=snapshot_date,
    )

    logger.info("Prepared %s developer analytics records.", len(records))
    return records


def export_analytics_to_clickhouse(
    events: list[dict],
    snapshot_date: date | str,
    client=None,
    inactivity_threshold_minutes: int = 15,
) -> dict:
    """Build analytics records and submit them to ClickHouse.

    Pass an existing client for testing or when reusing a connection.
    If no client is supplied, a new client is created.

    Returns a summary containing processed events and submitted records.
    """

    records = build_analytics_records(
        events=events,
        snapshot_date=snapshot_date,
        inactivity_threshold_minutes=inactivity_threshold_minutes,
    )

    if not records:
        return {
            "input_events": len(events),
            "analytics_records": 0,
            "inserted_records": 0,
            "status": "no_data",
        }

    if client is None:
        client = create_clickhouse_client()

    inserted_count = insert_developer_analytics(client, records)

    logger.info(
        "Analytics export finished: %s records submitted.",
        inserted_count,
    )

    return {
        "input_events": len(events),
        "analytics_records": len(records),
        "inserted_records": inserted_count,
        "status": "success",
    }