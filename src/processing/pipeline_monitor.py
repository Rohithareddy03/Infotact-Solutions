"""Monitoring utilities for the CogniStream analytics pipeline."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any


logger = logging.getLogger(__name__)


def create_execution_report(
    input_events: int,
    analytics_records: int,
    inserted_records: int,
    status: str,
    duration_seconds: float,
    error: str | None = None,
) -> dict:
    """Create a structured report for one pipeline execution."""

    if status not in {"success", "no_data", "failed"}:
        raise ValueError("Invalid pipeline status.")

    if min(input_events, analytics_records, inserted_records) < 0:
        raise ValueError("Record counts cannot be negative.")

    if duration_seconds < 0:
        raise ValueError("Duration cannot be negative.")

    return {
        "execution_time": datetime.now(timezone.utc).isoformat(),
        "input_events": input_events,
        "analytics_records": analytics_records,
        "inserted_records": inserted_records,
        "status": status,
        "duration_seconds": round(duration_seconds, 3),
        "error": error,
    }


def save_execution_report(
    report: dict,
    output_dir: str | Path = "logs/reports",
) -> Path:
    """Save an execution report as a JSON file."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )
    report_path = directory / f"pipeline_report_{timestamp}.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    logger.info("Pipeline execution report saved: %s", report_path)

    return report_path


def monitor_pipeline(
    pipeline_function: Callable[..., dict],
    *args: Any,
    report_dir: str | Path = "logs/reports",
    **kwargs: Any,
) -> dict:
    """Execute a pipeline function and save its monitoring report."""

    start_time = time.perf_counter()

    try:
        result = pipeline_function(*args, **kwargs)

        duration = time.perf_counter() - start_time

        if not isinstance(result, dict):
            raise TypeError("Pipeline function must return a dictionary.")

        status = result.get("status", "success")

        if status not in {"success", "no_data"}:
            raise ValueError("Pipeline returned an invalid status.")

        report = create_execution_report(
            input_events=result.get("input_events", 0),
            analytics_records=result.get("analytics_records", 0),
            inserted_records=result.get("inserted_records", 0),
            status=status,
            duration_seconds=duration,
        )

        save_execution_report(report, report_dir)

        logger.info(
            "Pipeline completed with status=%s in %.3f seconds.",
            status,
            duration,
        )

        return report

    except Exception as exc:
        duration = time.perf_counter() - start_time

        report = create_execution_report(
            input_events=0,
            analytics_records=0,
            inserted_records=0,
            status="failed",
            duration_seconds=duration,
            error=str(exc),
        )

        save_execution_report(report, report_dir)

        logger.exception("Pipeline execution failed.")

        raise