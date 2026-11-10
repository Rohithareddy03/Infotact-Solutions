# Source-Wise Ingestion Quality Reporting

## Overview

CogniStream generates source-wise ingestion quality statistics to monitor
the quality of developer activity events received from GitHub, Jira, Slack,
and ActivityWatch.

The report uses observable event validation results. It does not measure
developers' actual cognitive state.

## Reported Metrics

Each source reports:

- `total_events`: Number of received events.
- `accepted_events`: Number of successfully validated and accepted events.
- `invalid_events`: Number of events rejected due to schema or timestamp errors.
- `duplicate_events`: Number of repeated event records rejected.
- `rejected_events`: Total invalid and duplicate event records.
- `error_reasons`: Validation and duplicate error counts grouped by reason.

## Source Categories

The report includes:

- `github`
- `jira`
- `slack`
- `activitywatch`
- `unknown`

Missing or unsupported source values are grouped under `unknown` so that
invalid records remain visible in the quality report.

## Airflow Integration

The ingestion task calls `validate_event_batch()` and includes the
`source_quality` statistics in its `quality_summary`.

The summary is pushed to Airflow XCom and included in the pipeline
monitoring metadata.

## Duplicate Handling

The first valid occurrence of an event ID is accepted. Subsequent
occurrences are counted as duplicate events and included in rejected
event statistics.

## Validation and Testing

Unit tests verify:

1. Accepted event counts by source.
2. Invalid event counts by source.
3. Duplicate event counts by source.
4. Validation failure reasons.
5. Missing and unsupported source handling.
6. Availability of all source categories.

The complete project test suite passed with 158 tests during Day 24
validation.
