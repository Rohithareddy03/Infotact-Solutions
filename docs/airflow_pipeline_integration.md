# Airflow Pipeline Integration - CogniStream

## 1. Overview
CogniStream uses Apache Airflow to orchestrate the developer activity analytics pipeline. The daily DAG coordinates event ingestion, validation, analytics processing, monitoring, and export.

## 2. Input Data
The current DAG reads sample events from:
`data/sample/developer_events.json`

The path is resolved relative to the repository root so the DAG does not depend on the current terminal directory.

The sample data is simulated and is used for development and testing.

## 3. DAG Workflow
DAG ID: `cognistream_developer_analytics`

Schedule: `@daily`

The workflow contains two main tasks:

### Task 1: ingest_events
- Loads events using the file loader.
- Validates event records and required fields.
- Separates accepted and rejected events.
- Shares accepted events and quality information through Airflow XCom.

### Task 2: process_and_export
- Retrieves accepted events and quality information.
- Calls the analytics processing and ClickHouse export function.
- Runs the operation through the pipeline monitoring utility.
- Records the processing status in Airflow XCom.

Task dependency:

`ingest_events >> process_and_export`

## 4. Processing and Monitoring
The processing layer uses Python and Polars-based modules to prepare developer activity analytics. Supporting modules calculate activity blocks, developer metrics, and context-switching indicators.

The monitoring utility records pipeline status, execution duration, timestamps, results, and errors. Reports are saved under:

`logs/reports/`

## 5. Reliability
The DAG is configured with retries and a retry delay to handle temporary task failures. Catchup is disabled to avoid automatically processing historical scheduled runs.

## 6. ClickHouse Export
The analytics pipeline prepares aggregated records for ClickHouse. A reachable and correctly configured ClickHouse instance is required for a successful live export.

## 7. Testing
The project includes tests for ingestion, data validation, processing, analytics, ClickHouse preparation/export, and pipeline monitoring.

Python compilation and unit tests do not by themselves prove that the DAG has run successfully inside an Airflow environment.

## 8. Current Limitations
- The included JSON events are simulated sample data.
- Live GitHub, Jira, Slack, and ActivityWatch extraction is not demonstrated by this sample-file DAG.
- Actual Airflow execution requires a configured Airflow environment.
- Live ClickHouse export requires a reachable ClickHouse server and valid configuration.
- Analytics represent observable activity-based indicators, not direct measurements of a developer's cognitive state.
