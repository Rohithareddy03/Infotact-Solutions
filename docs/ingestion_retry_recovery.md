
# Day 27 – Ingestion Pipeline Retry and Recovery

## 1. Objective

Improve the reliability of the CogniStream developer activity ingestion pipeline by introducing retry and recovery handling for temporary file-access failures.

## 2. Problem

Previously, the ingestion pipeline attempted to load an event file only once. If a temporary file-access error occurred, the pipeline stopped immediately.

This could interrupt ingestion even when the problem might resolve after a short delay.

## 3. Implementation

Added a retry mechanism in:

`src/ingestion/pipeline.py`

The new `load_events_with_retry()` function supports:

- A configurable maximum number of attempts.
- A configurable delay between attempts.
- Logging for every failed attempt.
- Successful recovery when a later attempt succeeds.
- Error propagation when all attempts fail.

The existing `process_event_file()` function now uses this retry mechanism.

## 4. Error Handling Strategy

| Error | Retry behaviour |
|---|---|
| Temporary OSError | Retry |
| FileNotFoundError | Do not retry |
| Invalid JSON / ValueError | Do not retry |
| Empty file | Do not retry |
| Invalid event structure | Do not retry |

The default configuration allows three attempts with a one-second delay between attempts.

## 5. Automated Testing

Added retry-related tests in:

`tests/test_pipeline.py`

The tests cover:

1. Recovery after a temporary file-access failure.
2. Failure after all retry attempts are exhausted.
3. No retry for missing files.
4. Rejection of invalid retry-attempt values.
5. Rejection of negative retry delays.

Existing ingestion pipeline tests are retained.

## 6. Validation

The following checks were performed:

- Pipeline-specific tests.
- Complete project test suite.
- Git whitespace validation using `git diff --check`.

Test execution results should be recorded from the actual test run.

## 7. Benefits

- Improves ingestion reliability.
- Handles temporary file-access problems.
- Prevents unnecessary retries for permanent input errors.
- Provides useful logs for troubleshooting.
- Keeps existing pipeline usage compatible.

## 8. Scope and Limitations

This implementation retries local file-loading operations that raise `OSError`. It does not implement distributed recovery, automatic Airflow task retries, or retries for GitHub, Jira, Slack, or ActivityWatch API requests.

The sample developer activity data remains simulated.
