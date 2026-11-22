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


# ---------------------------------------------------------
# DATE VALIDATION
# ---------------------------------------------------------

def validate_date_range(start_date, end_date):
    """Validate dates in YYYY-MM-DD format."""

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


def _get_parameters(start_date, end_date, developer_id=None):
    """Prepare parameterized ClickHouse query values."""

    start, end = validate_date_range(
        start_date,
        end_date,
    )

    end_exclusive = (
        date.fromisoformat(end) + timedelta(days=1)
    ).isoformat()

    parameters = {
        "start_date": start,
        "end_date": end,
        "end_date_exclusive": end_exclusive,
    }

    if developer_id is not None:
        if not isinstance(developer_id, str) or not developer_id.strip():
            raise ValueError(
                "developer_id must be a non-empty string"
            )

        parameters["developer_id"] = developer_id.strip()

    return parameters


# ---------------------------------------------------------
# EXISTING POLARS QUERY FUNCTIONS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# STRUCTURED QUERY EXECUTION
# ---------------------------------------------------------

def execute_structured_query(
    client,
    query,
    parameters,
):
    """
    Execute a query and return structured dictionary results.

    Database errors are returned in a consistent error response.
    """

    try:
        result = client.query(
            query,
            parameters=parameters,
        )

        rows = [
            dict(zip(result.column_names, row))
            for row in result.result_rows
        ]

        return {
            "status": "success",
            "data": rows,
            "error": None,
        }

    except Exception as error:
        return {
            "status": "error",
            "data": [],
            "error": str(error),
        }


def _run_metric_query(
    query,
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Validate filters and execute a structured analytics query."""

    parameters = _get_parameters(
        start_date,
        end_date,
        developer_id,
    )

    # Only this fixed SQL fragment is added dynamically.
    # The developer ID itself is always passed as a bound parameter.
    if developer_id is not None:
        query = query.replace(
            "/* DEVELOPER_FILTER */",
            "AND developer_id = {developer_id:String}",
        )
    else:
        query = query.replace(
            "/* DEVELOPER_FILTER */",
            "",
        )

    try:
        if client is None:
            client = create_clickhouse_client()

    except Exception as error:
        return {
            "status": "error",
            "data": [],
            "error": str(error),
        }

    return execute_structured_query(
        client,
        query,
        parameters,
    )


# ---------------------------------------------------------
# 1. TOTAL DEVELOPER COMMITS
# ---------------------------------------------------------

def get_total_developer_commits(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Get total commits grouped by developer."""

    query = """
        SELECT
            developer_id,
            sum(total_commits) AS total_commits
        FROM cognistream.developer_daily_metrics
        WHERE metric_date BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY developer_id
        ORDER BY total_commits DESC
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# ---------------------------------------------------------
# 2. ESTIMATED ACTIVITY DURATION
# ---------------------------------------------------------

def get_activity_duration(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """
    Get estimated activity duration in minutes.

    The schema stores estimated_activity_minutes. It does not
    provide a separate IDE-only duration column.
    """

    query = """
        SELECT
            developer_id,
            round(
                sum(estimated_activity_minutes),
                2
            ) AS estimated_activity_minutes
        FROM cognistream.developer_daily_metrics
        WHERE metric_date BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY developer_id
        ORDER BY estimated_activity_minutes DESC
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# ---------------------------------------------------------
# 3. AVERAGE SESSION DURATION
# ---------------------------------------------------------

def get_average_session_duration(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Get average session duration in minutes."""

    query = """
        SELECT
            developer_id,
            count() AS session_count,
            round(avg(duration_minutes), 2)
                AS average_session_minutes
        FROM cognistream.developer_sessions
        WHERE toDate(session_start) BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY developer_id
        ORDER BY average_session_minutes DESC
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# ---------------------------------------------------------
# 4. UNINTERRUPTED ACTIVITY BLOCKS
# ---------------------------------------------------------

def get_uninterrupted_activity_blocks(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Get qualifying uninterrupted activity blocks."""

    query = """
        SELECT
            developer_id,
            countIf(qualifies = 1)
                AS uninterrupted_block_count,
            round(
                sumIf(duration_minutes, qualifies = 1),
                2
            ) AS uninterrupted_duration_minutes
        FROM cognistream.flow_blocks
        WHERE toDate(block_start) BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY developer_id
        ORDER BY uninterrupted_block_count DESC
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# ---------------------------------------------------------
# 5. CONTEXT-SWITCH FREQUENCY
# ---------------------------------------------------------

def get_context_switch_frequency(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Get context-switch counts grouped by developer."""

    query = """
        SELECT
            developer_id,
            count() AS context_switch_count
        FROM cognistream.context_switches
        WHERE toDate(from_timestamp) BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY developer_id
        ORDER BY context_switch_count DESC
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# ---------------------------------------------------------
# 6. INTERRUPTION COUNT
# ---------------------------------------------------------

def get_interruption_count(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Get potential interruption counts grouped by developer."""

    query = """
        SELECT
            developer_id,
            count() AS interruption_count
        FROM cognistream.potential_interruptions
        WHERE toDate(interruption_timestamp) BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY developer_id
        ORDER BY interruption_count DESC
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# ---------------------------------------------------------
# 7. DAILY DEVELOPER ACTIVITY SUMMARY
# ---------------------------------------------------------

def get_daily_activity_summary(
    start_date,
    end_date,
    developer_id=None,
    client=None,
):
    """Get daily activity summaries for each developer."""

    query = """
        SELECT
            metric_date,
            developer_id,
            sum(total_events) AS total_events,
            sum(total_commits) AS total_commits,
            sum(total_sessions) AS total_sessions,
            round(
                sum(estimated_activity_minutes),
                2
            ) AS estimated_activity_minutes,
            sum(total_context_switches)
                AS total_context_switches,
            sum(total_blocks) AS total_blocks,
            sum(qualifying_blocks) AS qualifying_blocks,
            round(
                sum(estimated_flow_minutes),
                2
            ) AS estimated_flow_minutes,
            sum(potential_interruptions)
                AS potential_interruptions
        FROM cognistream.developer_daily_metrics
        WHERE metric_date BETWEEN
            {start_date:Date} AND {end_date:Date}
            /* DEVELOPER_FILTER */
        GROUP BY
            metric_date,
            developer_id
        ORDER BY
            metric_date,
            developer_id
    """

    return _run_metric_query(
        query,
        start_date,
        end_date,
        developer_id,
        client,
    )


# Alias for callers that use the task's IDE activity terminology.
# This returns the schema's estimated activity duration, not an
# independently measured IDE-only duration.
get_ide_activity_duration = get_activity_duration