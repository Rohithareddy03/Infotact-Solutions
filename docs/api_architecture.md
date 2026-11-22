# CogniStream API Architecture

## Architecture Overview

The API acts as a communication layer between
the ClickHouse database and React dashboard.

## Data Flow

1. Airflow orchestrates data ingestion.
2. Python and Polars process developer events.
3. ClickHouse stores analytics data.
4. FastAPI retrieves analytics from ClickHouse.
5. React dashboard displays analytics to users.

## API Responsibilities

- Receive frontend requests.
- Validate request parameters.
- Retrieve analytics from ClickHouse.
- Return structured JSON responses.
- Handle errors and invalid requests.

## Security Considerations

- Keep database credentials in environment variables.
- Do not expose database credentials through API responses.
- Validate incoming parameters.
- Handle exceptions without exposing sensitive details.