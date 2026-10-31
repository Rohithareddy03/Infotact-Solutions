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