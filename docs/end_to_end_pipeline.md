# CogniStream End-to-End Data Pipeline

## Objective

Coordinate the existing data engineering components
into one reusable workflow.

## Module

src/ingestion/end_to_end_pipeline.py

## Pipeline stages

1. Load developer activity events.
2. Validate the complete event batch.
3. Separate accepted and rejected events.
4. Export accepted events and quality information
   to the ClickHouse export component.
5. Execute pipeline monitoring.
6. Return an execution summary.

## Execution statuses

- success: All events were accepted and the workflow completed.
- partial: The workflow completed but some events were rejected.

Exceptions from loading, validation, export, or monitoring
are propagated to the caller.

## Integration

The coordinator accepts existing pipeline functions
as callable arguments. This allows the Airflow DAG
or another execution environment to supply the
appropriate implementations.

Check actual function signatures before integration.

## Testing

Run from the project root:

python -m unittest discover -s tests -p
"test_end_to_end_pipeline.py" -v

The automated tests use mocked components.
Live ClickHouse export and Airflow execution
must be verified separately.