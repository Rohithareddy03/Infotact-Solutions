
# CogniStream — Apache Airflow Pipeline

# 1. Purpose

Apache Airflow will orchestrate the scheduled ingestion of developer
activity events for the CogniStream analytics platform.

The pipeline will coordinate extraction, validation, and downstream
data preparation tasks.

# 2. Planned Data Sources

- GitHub API
- Jira API
- Slack API or authorized event exports
- VS Code ActivityWatch API or exported activity logs

The availability of each source depends on credentials, permissions,
and local configuration.

# 3. Proposed DAG Workflow

The initial DAG is planned to execute the following stages:

1. Start the ingestion workflow.
2. Extract available GitHub activity events.
3. Extract available Jira activity events.
4. Extract authorized Slack activity events.
5. Retrieve available ActivityWatch events.
6. Validate and normalize extracted event records.
7. Record execution results and errors.
8. Pass validated data to downstream processing and storage.
9. Mark the workflow as successful or failed.

Independent source extraction tasks may run in parallel when appropriate.

# 4. Scheduling Strategy

The ingestion workflow will use a configurable schedule.

The initial schedule will be selected after evaluating API rate limits,
data availability, and project infrastructure.

Historical backfills and manual DAG runs may be used for testing.

# 5. Error Handling

The workflow should support:

- Logging extraction failures.
- Configurable retries for transient errors.
- Handling API rate limits and timeouts.
- Recording task execution status.
- Preventing invalid data from silently entering the pipeline.
- Avoiding duplicate event ingestion where possible.

# 6. Downstream Integration

After validation, the extracted records will be prepared for processing
with Python and Polars.

Validated and processed events will then be loaded into ClickHouse
according to the agreed database schema.

The exact task dependencies will be finalized during implementation.

# 7. Configuration

Configuration may include:

- API credentials
- API endpoints
- Request timeouts
- Retry settings
- Ingestion schedule
- Database connection settings

Sensitive values must be provided through environment variables or
an approved secret manager.

Credentials must never be hardcoded into DAG files or committed to GitHub.

# 8. Testing Strategy

The pipeline will be tested using:

- Sample developer activity events
- Successful extraction scenarios
- Missing or invalid event fields
- API timeout and failure scenarios
- Duplicate event scenarios
- Downstream processing and loading checks

External integrations should be tested only with authorized access.

# 9. Implementation Milestones

Week 1:
Develop extraction scripts and the initial Airflow DAG.

Week 2:
Integrate event validation and downstream data loading.

Week 3:
Support dashboard development by providing reliable analytical data.

Week 4:
Complete end-to-end integration, testing, and documentation.

# 10. Current Status

This document describes the planned Airflow architecture.
The DAG, operators, schedules, and connections will be implemented
and validated in subsequent development tasks.
