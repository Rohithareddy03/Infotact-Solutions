# CogniStream - Developer Flow-State & Cognitive Load Analytics

## 1. Project Overview

CogniStream is a developer activity analytics system designed to analyze observable software development activities and present indicators related to developer workflow patterns.

It processes activity events from sources such as GitHub, Jira, Slack, and IDE activity-monitoring tools. The system organizes these events into analytical metrics, including activity duration, uninterrupted work blocks, context switching, and interruptions.

**Important:** CogniStream does not directly measure a person's mental state or cognitive load. It uses observable activity-based indicators as estimates of workflow patterns.

## 2. Project Objectives

- Collect developer activity events from multiple sources.
- Validate and clean incoming event data.
- Identify activity sessions and uninterrupted work blocks.
- Analyze context switches and interruption patterns.
- Store structured analytical data in ClickHouse.
- Present meaningful developer activity insights through a dashboard.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion and processing |
| Apache Airflow | Pipeline orchestration |
| Polars | Data transformation and analytics |
| ClickHouse | Analytical database |
| FastAPI | Backend API |
| React | Frontend dashboard |
| Tremor.js | Dashboard visualizations |
| Pytest | Automated testing |

## 4. Project Architecture

The intended data flow is:

1. **Data Sources:** GitHub, Jira, Slack, and ActivityWatch.
2. **Ingestion:** Collect activity events and load JSON data.
3. **Validation:** Check event structure, required fields, and data quality.
4. **Processing:** Clean, normalize, deduplicate, and analyze events.
5. **Analytics:** Calculate activity blocks, context switches, interruptions, and developer metrics.
6. **Storage:** Prepare and export analytical data to ClickHouse.
7. **API and Dashboard:** Expose analytics through FastAPI and display them using React and Tremor.js.

## 5. Repository Structure

```text
CogniStream/
├── airflow/
│   └── dags/
├── data/
│   └── sample/
├── docs/
├── SQL/
├── src/
│   ├── database/
│   ├── ingestion/
│   └── processing/
├── tests/
├── requirements.txt
└── README.md
```

## 6. Current Implemented Components

### Data Ingestion
- JSON event loading.
- Event validation.
- Ingestion pipeline.
- Data quality checks.
- Retry and recovery for temporary file-access failures.

### Data Processing
- Event transformation and deduplication.
- Activity block calculation.
- Context-switch analysis.
- Developer activity metrics.
- Unified analytics processing.
- Pipeline monitoring and observability.

### Database
- ClickHouse client integration.
- Analytics schema.
- Data preparation and export modules.

### Orchestration
- Airflow DAG definition for the analytics pipeline.

### Testing
- Automated tests for ingestion, processing, analytics, database integration, and pipeline reliability.

## 7. Activity Metrics

CogniStream is designed to calculate:

- **Commit Count:** Number of commit events in a selected period.
- **IDE Activity Duration:** Duration of qualifying IDE activity intervals.
- **Uninterrupted Activity Blocks:** Continuous qualifying coding activity without a defined interruption.
- **Context Switches:** Transitions between tracked applications or activity contexts.
- **Interruption Rate:** Number of detected interruptions relative to a defined time or session period.
- **Average Session Duration:** Total qualifying activity duration divided by the number of sessions.

Metric values depend on event quality, session definitions, and configured thresholds.

## 8. Installation and Setup

### Prerequisites

- Python 3.10 or later.
- Git.
- ClickHouse, if database integration is required.
- Apache Airflow in a supported environment, if DAG execution is required.

### Clone the Repository

```bash
git clone https://github.com/Rohithareddy03/Infotact-Solutions.git
cd Infotact-Solutions
```

### Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

## 9. Running Tests

Run the complete automated test suite:

```bash
python -m pytest -v
```

Check Python syntax for the Airflow DAG:

```bash
python -m py_compile airflow/dags/cognistream_analytics_dag.py
```

A successful syntax check does not by itself confirm that the DAG has executed in an Airflow environment.

## 10. Sample Data

Sample developer activity events are available in:

`data/sample/developer_events.json`

The sample data is simulated for development and testing. It should not be treated as actual developer activity.

## 11. Documentation

Additional technical documentation is available in the `docs/` directory, including:

- End-to-end pipeline integration.
- Ingestion quality and failure testing.
- Retry and recovery handling.
- Pipeline monitoring and reliability.
- Source quality reporting.

## 12. Limitations

- Activity-based indicators are estimates and do not directly measure cognitive state.
- Analytics depend on the completeness and accuracy of available events.
- Sample data is simulated.
- External source integrations require appropriate credentials and configuration.
- Airflow orchestration and ClickHouse deployment require their respective runtime environments.
- Frontend and API components may be maintained in separate team branches.

## 13. Team Project

**Project:** CogniStream – Developer Flow-State & Cognitive Load Analytics

**Team size:** 4 members

This project was developed as a collaborative assignment using Git and GitHub with individual team branches.
