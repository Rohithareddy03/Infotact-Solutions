# CogniStream Pipeline Monitoring

## Purpose

Track the execution of the developer analytics pipeline and
record structured execution reports.

## Monitored information

- Input event count
- Prepared analytics record count
- Submitted ClickHouse record count
- Pipeline execution status
- Execution duration in seconds
- Error message when execution fails
- UTC execution timestamp

## Execution statuses

| Status | Meaning |
|---|---|
| success | Analytics records were submitted successfully |
| no_data | No analytics records were available |
| failed | Pipeline execution encountered an error |

## Report storage

Reports are saved as JSON files under:

logs/reports/

Each execution creates a separate report file.

## Usage

The monitor can wrap the analytics export function:

```python
from src.processing.analytics_pipeline import (
    export_analytics_to_clickhouse,
)
from src.processing.pipeline_monitor import monitor_pipeline

report = monitor_pipeline(
    export_analytics_to_clickhouse,
    events,
    "2026-10-31",
)


## Day 20 - Enhanced Pipeline Observability

### Objective

Improve pipeline monitoring by recording execution metrics,
Airflow metadata, ingestion-quality statistics, and failure details.

### New Module

`src/processing/pipeline_observability.py`

### Features

1. Unique execution ID for every pipeline run.
2. Pipeline name and execution status.
3. UTC start and completion timestamps.
4. Pipeline execution duration.
5. Input event count.
6. Analytics record count.
7. Inserted record count.
8. Airflow DAG and task metadata.
9. Ingestion-quality statistics.
10. Failure type and error message.
11. JSON execution report generation.

### Execution Status

- success: Pipeline completed successfully.
- no_data: Pipeline completed without analytics data.
- failed: Pipeline raised an exception.

### Report Storage

Execution reports are saved in:

`logs/reports/`

Each report is stored as a separate JSON file
using its unique execution ID.

### Testing

Unit tests cover successful runs, empty runs,
failed runs, metadata persistence, metric extraction,
execution duration, and JSON report creation.

### Limitations

- Monitoring records observable pipeline execution,
  not developer cognitive state.
- Airflow worker storage must be configured so reports
  are retained and accessible.
- A saved report does not independently verify that
  ClickHouse permanently stored the inserted records.