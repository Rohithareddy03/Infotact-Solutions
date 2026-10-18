
# CogniStream — Developer Event Ingestion

# 1. Overview

CogniStream is a Developer Flow-State and Cognitive Load Analytics
project designed to analyze developer activity patterns, uninterrupted
work sessions, and context-switching events.

The ingestion module is responsible for collecting timestamped developer
activity events from multiple sources and preparing them for downstream
data processing and analytics.

# 2. Objectives

- Identify and document supported developer activity data sources.
- Collect timestamped events from authorized APIs and local activity logs.
- Standardize events into a common structure.
- Validate event timestamps and required fields.
- Prepare data for processing with Python and Polars.
- Support scheduled ingestion through Apache Airflow.
- Provide clean event data for storage and analysis in ClickHouse.

# 3. Data Sources

# 3.1 GitHub

Purpose:
Collect development activity associated with repositories.

Planned events:
- Commit activity
- Pull request activity
- Repository activity timestamps

Expected output:
Developer activity events with source identifiers and timestamps.

# 3.2 Jira

Purpose:
Understand task-related development activity.

Planned events:
- Issue creation and updates
- Issue status transitions
- Task activity timestamps

Access requirements:
An authorized Jira account and appropriate API permissions.

# 3.3 Slack

Purpose:
Analyze potential communication-related interruptions.

Planned events:
- Authorized message or notification event timestamps
- Permitted event metadata

Access requirements:
Approved Slack API permissions and access to the required event data.

Only the minimum required metadata should be collected. Message contents
should not be collected unless explicitly required and authorized.

# 3.4 VS Code ActivityWatch

Purpose:
Analyze IDE activity and application usage patterns.

Planned events:
- Application activity intervals
- Active-window timestamps
- Available editor activity metadata

Access requirements:
A compatible ActivityWatch installation and access to its local API
or exported activity data.

ActivityWatch availability and the exact event fields must be verified
during implementation.

# 4. Common Event Schema

Events from different sources will be normalized into a common structure.

| Field | Description |
|---|---|
| event_id | Unique event identifier |
| developer_id | Pseudonymous developer identifier |
| source | Origin of the event |
| event_type | Type of activity |
| event_timestamp | Event timestamp in UTC |
| metadata | Source-specific event attributes |

Example:

    {
      "event_id": "evt_001",
      "developer_id": "dev_001",
      "source": "github",
      "event_type": "commit",
      "event_timestamp": "2026-10-18T10:30:00Z",
      "metadata": {
        "repository": "sample-repo"
      }
    }

The example represents sample data, not a real developer event.

# 5. Ingestion Workflow

1. Connect to an authorized data source.
2. Retrieve available activity events.
3. Validate required fields and timestamps.
4. Normalize timestamps to UTC.
5. Identify duplicate or invalid events.
6. Prepare records for downstream processing.
7. Pass validated events to the processing and loading pipeline.
8. Record ingestion status and errors.

# 6. Data Validation Requirements

- Required fields must be present.
- Event timestamps must use a consistent format.
- Source names must be recognized.
- Duplicate events should be identified.
- Invalid records should be logged and handled safely.
- Missing optional metadata should not automatically invalidate an event.
- API failures and rate limits should be handled appropriately.

# 7. Integration with Other Modules

Apache Airflow:
Schedules and orchestrates ingestion tasks.

Python:
Implements source-specific extraction and validation.

Polars:
Performs downstream data cleaning and transformation.

ClickHouse:
Stores event records for analytical queries.

FastAPI:
Serves aggregated analytics to the dashboard.

React and Tremor.js:
Display the resulting analytics and visualizations.

# 8. Configuration and Security

- Store credentials in environment variables or an approved secret manager.
- Never commit API tokens, passwords, or private credentials.
- Provide an .env.example file containing placeholder values only.
- Follow source API permissions and rate limits.
- Collect only data required for the project's analytics.
- Use pseudonymous identifiers where possible.

# 9. Development Plan

Day 1:
Document data sources, event schema, and ingestion requirements.

Week 1:
Implement extraction scripts, sample event generation, and the initial
Airflow ingestion workflow.

Later phases:
Integrate validated events with Polars processing and ClickHouse storage.

# 10. Current Status

This document defines the planned ingestion design.
Individual source integrations and Airflow tasks must be implemented
and tested before they can be considered operational.
