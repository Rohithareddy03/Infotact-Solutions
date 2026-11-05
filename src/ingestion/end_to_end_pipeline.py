import logging
from pathlib import Path
from typing import Callable, Any


logger = logging.getLogger(__name__)


def run_end_to_end_pipeline(
    input_file: str,
    load_events: Callable,
    validate_event_batch: Callable,
    export_analytics_to_clickhouse: Callable,
    monitor_pipeline: Callable,
) -> dict[str, Any]:
    """
    Coordinate event loading, validation, ClickHouse export,
    and pipeline monitoring.

    The callable interfaces expected are:

    load_events(input_file) -> list of event dictionaries

    validate_event_batch(events) -> quality summary dictionary

    export_analytics_to_clickhouse(
        accepted_events=...,
        quality_summary=...
    ) -> export result

    monitor_pipeline(
        quality_summary=...,
        export_result=...
    ) -> monitoring result

    Returns a compact pipeline execution summary.
    """

    file_path = Path(input_file)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Input path is not a file: {file_path}"
        )

    logger.info("Starting end-to-end ingestion pipeline")

    # Step 1: Load events.
    events = load_events(str(file_path))

    if not isinstance(events, list):
        raise TypeError("load_events must return a list")

    if not events:
        raise ValueError("No events found in input file")

    logger.info("Loaded %d events", len(events))

    # Step 2: Validate the event batch.
    quality_summary = validate_event_batch(events)

    if not isinstance(quality_summary, dict):
        raise TypeError(
            "validate_event_batch must return a dictionary"
        )

    required_keys = {
        "total_events",
        "valid_events",
        "invalid_events",
        "accepted_events",
        "rejected_events",
    }

    missing_keys = required_keys - set(quality_summary)

    if missing_keys:
        raise ValueError(
            f"Quality summary is missing keys: {sorted(missing_keys)}"
        )

    accepted_events = quality_summary["accepted_events"]

    if not isinstance(accepted_events, list):
        raise TypeError("accepted_events must be a list")

    logger.info(
        "Validation complete: %d accepted, %d rejected",
        len(accepted_events),
        len(quality_summary["rejected_events"]),
    )

    # Step 3: Export accepted events and quality information.
    export_result = export_analytics_to_clickhouse(
        accepted_events=accepted_events,
        quality_summary=quality_summary,
    )

    logger.info("ClickHouse export function completed")

    # Step 4: Monitor the execution.
    monitoring_result = monitor_pipeline(
        quality_summary=quality_summary,
        export_result=export_result,
    )

    logger.info("Pipeline monitoring completed")

    rejected_count = len(quality_summary["rejected_events"])

    if rejected_count:
        status = "partial"
    else:
        status = "success"

    return {
        "status": status,
        "input_file": str(file_path),
        "total_events": quality_summary["total_events"],
        "valid_events": quality_summary["valid_events"],
        "invalid_events": quality_summary["invalid_events"],
        "accepted_events": len(accepted_events),
        "rejected_events": rejected_count,
        "export_result": export_result,
        "monitoring_result": monitoring_result,
    }