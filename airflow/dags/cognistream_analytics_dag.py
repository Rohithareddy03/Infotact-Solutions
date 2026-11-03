"""Airflow DAG for the CogniStream analytics workflow."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from src.ingestion.file_loader import load_events
from src.ingestion.quality_checks import validate_event_batch
from src.processing.analytics_pipeline import (
    export_analytics_to_clickhouse,
)
from src.processing.pipeline_observability import (
    run_monitored_pipeline,
)


SAMPLE_FILE = "data/sample/events.json"


def ingest_developer_events(**context):
    """Load events, validate them, and remove duplicate IDs."""

    events = load_events(SAMPLE_FILE)

    if not isinstance(events, list):
        raise ValueError("Ingestion must return a list of events.")

    quality_report = validate_event_batch(events)

    if not quality_report["valid_events"]:
        raise ValueError(
            "No valid developer activity events were available."
        )

    ti = context["ti"]

    # Pass only the accepted event collection to the next task.
    ti.xcom_push(
        key="accepted_events",
        value=quality_report["valid_events"],
    )

    # Pass the quality summary separately for monitoring.
    quality_summary = {
        "total_events": quality_report["total_events"],
        "accepted_events": quality_report["accepted_events"],
        "rejected_events": quality_report["rejected_events"],
        "duplicate_extra_rows": quality_report["duplicate_extra_rows"],
        "duplicate_event_ids": quality_report["duplicate_event_ids"],
    }

    ti.xcom_push(
        key="quality_summary",
        value=quality_summary,
    )

    return quality_summary


def process_and_export_events(**context):
    """Process validated events and export analytics."""

    ti = context["ti"]

    events = ti.xcom_pull(
        task_ids="ingest_events",
        key="accepted_events",
    )

    if not events:
        raise ValueError("No validated events received.")

    quality_summary = ti.xcom_pull(
        task_ids="ingest_events",
        key="quality_summary",
    )

    report = monitor_pipeline(
        export_analytics_to_clickhouse,
        events,
        context["ds"],
    )

    report["ingestion_quality"] = quality_summary

    ti.xcom_push(
        key="pipeline_status",
        value=report["status"],
    )

    return report


default_args = {
    "owner": "cognistream",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="cognistream_developer_analytics",
    description=(
        "Daily developer event validation, analytics, "
        "and ClickHouse export."
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