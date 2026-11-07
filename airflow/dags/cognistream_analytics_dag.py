"""Airflow DAG for the CogniStream analytics workflow."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.ingestion.file_loader import load_events
from src.ingestion.quality_checks import validate_event_batch
from src.processing.analytics_pipeline import export_analytics_to_clickhouse
from src.processing.pipeline_observability import run_monitored_pipeline

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_FILE = REPO_ROOT / "data" / "sample" / "developer_events.json"
REPORT_DIR = REPO_ROOT / "logs" / "reports"


def ingest_developer_events(**context):
    """Load, validate, and deduplicate developer activity events."""

    events = load_events(SAMPLE_FILE)
    quality_report = validate_event_batch(events)

    accepted_events = quality_report["valid_events"]

    if not accepted_events:
        raise ValueError("No valid developer activity events were available.")

    quality_summary = {
        "total_events": quality_report["total_events"],
        "accepted_events": quality_report["accepted_events"],
        "rejected_events": quality_report["rejected_events"],
        "duplicate_extra_rows": quality_report["duplicate_extra_rows"],
        "duplicate_event_ids": quality_report["duplicate_event_ids"],
    }

    ti = context["ti"]
    ti.xcom_push(key="accepted_events", value=accepted_events)
    ti.xcom_push(key="quality_summary", value=quality_summary)

    logger.info("Accepted %s events.", len(accepted_events))
    return quality_summary


def process_and_export_events(**context):
    """Process validated events and export analytics to ClickHouse."""

    ti = context["ti"]

    events = ti.xcom_pull(
        task_ids="ingest_events",
        key="accepted_events",
    )
    quality_summary = ti.xcom_pull(
        task_ids="ingest_events",
        key="quality_summary",
    )

    if not events:
        raise ValueError("No validated events received.")

    monitored_result = run_monitored_pipeline(
        export_analytics_to_clickhouse,
        events,
        context["ds"],
        report_dir=REPORT_DIR,
        report_metadata={
            "dag_id": context["dag"].dag_id,
            "run_id": context["run_id"],
            "execution_date": context["ds"],
            "ingestion_quality": quality_summary,
        },
    )

    report = monitored_result["report"]
    result = monitored_result["result"]

    ti.xcom_push(key="pipeline_status", value=report["status"])

    return {
        "status": report["status"],
        "analytics_result": result,
        "ingestion_quality": quality_summary,
        "monitoring_report": report,
    }


default_args = {
    "owner": "cognistream",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="cognistream_developer_analytics",
    description=(
        "Daily developer event ingestion, validation, "
        "analytics processing, and ClickHouse export."
    ),
    default_args=default_args,
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    catchup=False,
    tags=["cognistream", "analytics", "developer-activity"],
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_events",
        python_callable=ingest_developer_events,
    )

    analytics_task = PythonOperator(
        task_id="process_and_export",
        python_callable=process_and_export_events,
    )

    ingest_task >> analytics_task
