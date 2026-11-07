from datetime import date, timedelta
from pathlib import Path

import polars as pl

from src.database.clickhouse_connection import (
    create_clickhouse_client,
)


SQL_DIRECTORY = (
    Path(__file__).resolve().parents[2]
    / "sql"
    / "analytics"
)


def validate_date_range(start_date, end_date):
    """Validate the requested analytics date range."""

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

    except (TypeError, ValueError):
        raise ValueError(
            "Dates must use YYYY-MM-DD format"
        )

    if start.isoformat() != start_date:
        raise ValueError("Invalid start_date format")

    if end.isoformat() != end_date:
        raise ValueError("Invalid end_date format")

    if start > end:
        raise ValueError(
            "start_date cannot be after end_date"
        )

    return start.isoformat(), end.isoformat()


def execute_analytics_query(
    client,
    query: str,
    parameters: dict,
):
    """Execute a ClickHouse query and return a Polars DataFrame."""

    result = client.query(
        query,
        parameters=parameters,
    )

    return pl.DataFrame(
        result.result_rows,
        schema=result.column_names,
        orient="row",
    )


def _load_sql(filename):
    """Load an SQL analytics query from the SQL directory."""

    sql_path = SQL_DIRECTORY / filename

    if not sql_path.exists():
        raise FileNotFoundError(
            f"SQL query file not found: {sql_path}"
        )

    return sql_path.read_text(encoding="utf-8")


def _get_parameters(start_date, end_date):
    """Prepare safe ClickHouse query parameters."""

    start, end = validate_date_range(
        start_date,
        end_date,
    )

    end_exclusive = (
        date.fromisoformat(end) + timedelta(days=1)
    ).isoformat()

    return {
        "start_date": start,
        "end_date": end,
        "end_date_exclusive": end_exclusive,
    }


def get_developer_kpis(
    start_date,
    end_date,
    client=None,
):
    """Retrieve daily developer KPIs."""

    if client is None:
        client = create_clickhouse_client()

    query = _load_sql("developer_kpis.sql")

    parameters = _get_parameters(
        start_date,
        end_date,
    )

    return execute_analytics_query(
        client,
        query,
        {
            "start_date": parameters["start_date"],
            "end_date": parameters["end_date"],
        },
    )


def get_session_analysis(
    start_date,
    end_date,
    client=None,
):
    """Retrieve developer session statistics."""

    if client is None:
        client = create_clickhouse_client()

    query = _load_sql("session_analysis.sql")

    parameters = _get_parameters(
        start_date,
        end_date,
    )

    return execute_analytics_query(
        client,
        query,
        parameters,
    )


def get_interruption_analysis(
    start_date,
    end_date,
    client=None,
):
    """Retrieve potential developer interruptions."""

    if client is None:
        client = create_clickhouse_client()

    query = _load_sql("interruption_analysis.sql")

    parameters = _get_parameters(
        start_date,
        end_date,
    )

    return execute_analytics_query(
        client,
        query,
        parameters,
    )