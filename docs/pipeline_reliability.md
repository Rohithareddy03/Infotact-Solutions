## Pipeline Monitoring Reliability

## Objective
Improve the reliability of CogniStream pipeline monitoring by validating pipeline results and recording failures accurately.

## Changes Implemented

### 1. Pipeline Result Validation
- Verify that monitored pipeline functions return a dictionary.
- Raise a TypeError when the result is not a dictionary.
- Prevent invalid pipeline results from being treated as successful executions.

### 2. Pipeline Status Validation
- Accept only supported statuses: `success` and `no_data`.
- Raise a ValueError when an unsupported status is returned.
- Preserve valid pipeline execution statuses.

### 3. Failure Reporting
- Record failed execution status in the observability report.
- Store the exception type and error message.
- Save the JSON report before raising the pipeline failure.
- Preserve execution timestamps and duration information.

## Testing

Added `tests/test_pipeline_reliability.py`.

Test scenarios:
1. Non-dictionary pipeline result.
2. Invalid pipeline status.
3. Successful pipeline result.
4. No-data pipeline result.

Existing observability tests were also executed.

## Validation Results

- Focused monitoring tests: 14 passed.
- Complete project test suite: 162 passed.
- Python syntax compilation: passed.
- Git whitespace validation: passed.

## Expected Outcome

The monitoring system now detects invalid pipeline results instead of silently reporting them as successful. Failed executions are recorded in JSON reports for easier debugging and monitoring.

Note: These tests validate the Python monitoring logic. They do not represent execution of the DAG in a live Apache Airflow environment.
