import json
import logging
import time
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


logger = logging.getLogger(__name__)


def _utc_now() -> str:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _extract_result_metrics(result: Any) -> dict:
    """Extract useful pipeline metrics from a dictionary result."""
    if not isinstance(result, dict):
        return {}

    metric_names = (
        "input_events",
        "analytics_records",
        "inserted_records",
        "status",
    )

    return {
        key: result[key]
        for key in metric_names
        if key in result
    }


def save_observability_report(
    report: dict,
    output_dir: str | Path = "logs/reports",
) -> str:
    """Save an execution report as a JSON file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    run_id = report["run_id"]
    report_path = output_path / f"{run_id}.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, default=str)

    logger.info("Execution report saved: %s", report_path)

    return str(report_path)


def run_monitored_pipeline(
    pipeline_function: Callable,
    *args,
    report_dir: str | Path = "logs/reports",
    report_metadata: dict | None = None,
    **kwargs,
) -> dict:
    """
    Execute a pipeline function and save a complete execution report.

    Additional metadata is included before the report is saved.
    Pipeline exceptions are recorded and then re-raised.
    """
    run_id = str(uuid.uuid4())
    started_at = _utc_now()
    start_time = time.perf_counter()

    report = {
        "run_id": run_id,
        "pipeline_name": getattr(
            pipeline_function, "__name__", "unknown_pipeline"
        ),
        "status": "running",
        "started_at": started_at,
        "completed_at": None,
        "duration_seconds": None,
        "metrics": {},
        "metadata": report_metadata or {},
        "error": None,
        "report_path": None,
    }

    logger.info(
        "Starting monitored pipeline: %s",
        report["pipeline_name"],
    )

    try:
        result = pipeline_function(*args, **kwargs)

        report["metrics"] = _extract_result_metrics(result)

        result_status = (
            result.get("status")
            if isinstance(result, dict)
            else None
        )

        report["status"] = (
            result_status
            if result_status in {"success", "no_data"}
            else "success"
        )

        report["result"] = result

        return_value = result

    except Exception as exc:
        report["status"] = "failed"
        report["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

        logger.exception("Pipeline execution failed")

        return_value = None

    finally:
        report["completed_at"] = _utc_now()
        report["duration_seconds"] = round(
            time.perf_counter() - start_time,
            4,
        )

        try:
            report["report_path"] = save_observability_report(
                report,
                report_dir,
            )
        except Exception:
            logger.exception("Could not save execution report")

        logger.info(
            "Pipeline finished with status: %s",
            report["status"],
        )

    if report["status"] == "failed":
        error_message = report["error"]["message"]
        raise RuntimeError(
            f"Pipeline failed: {error_message}"
        )

    return {
        "report": report,
        "result": return_value,
    }