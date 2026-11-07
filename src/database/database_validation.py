
"""ClickHouse database structure and data-quality validation."""

import logging
from time import perf_counter

from src.database.clickhouse_connection import (
    create_clickhouse_client,
)

logger = logging.getLogger(__name__)

DATABASE_NAME = "cognistream"

# Fixed internal table and column definitions.
REQUIRED_TABLES = {
    "developer_events": [
        "event_id",
        "developer_id",
        "source",
        "event_type",
        "event_timestamp",
    ],
    "developer_sessions": [
        "developer_id",
        "session_start",
        "session_end",
        "event_count",
        "duration_minutes",
    ],
    "context_switches": [
        "developer_id",
        "from_source",
        "to_source",
        "from_timestamp",
        "to_timestamp",
    ],
    "flow_blocks": [
        "developer_id",
        "block_start",
        "block_end",
        "duration_minutes",
    ],
    "potential_interruptions": [
        "developer_id",
        "slack_event_id",
        "coding_event_id",
        "interruption_timestamp",
        "minutes_after_coding",
    ],
    "developer_daily_metrics": [
        "metric_date",
        "developer_id",
        "total_events",
        "total_commits",
        "total_sessions",
    ],
}


def _get_client(client=None):
    """Return the supplied client or create a new one."""
    return client if client is not None else create_clickhouse_client()


def check_database_connection(client=None):
    """Verify basic ClickHouse connectivity using SELECT 1."""
    try:
        client = _get_client(client)
        result = client.query("SELECT 1")
        return bool(
            result.result_rows
            and result.result_rows[0][0] == 1
        )
    except Exception:
        logger.exception("ClickHouse connection check failed.")
        return False


def check_query_performance(client=None):
    """Measure the execution time of a basic SELECT 1 query."""
    try:
        client = _get_client(client)

        start_time = perf_counter()
        result = client.query("SELECT 1")
        execution_time = (perf_counter() - start_time) * 1000

        success = bool(
            result.result_rows
            and result.result_rows[0][0] == 1
        )

        return {
            "success": success,
            "execution_time_ms": round(execution_time, 3),
        }

    except Exception as exc:
        logger.exception("Query performance check failed.")
        return {
            "success": False,
            "execution_time_ms": None,
            "error": str(exc),
        }


def validate_database(client=None):
    """
    Validate required tables, columns, and row counts.

    Returns a structured validation report.
    """
    client = _get_client(client)

    report = {
        "database": DATABASE_NAME,
        "tables": {},
        "missing_tables": [],
        "missing_columns": {},
        "total_records": 0,
        "overall_valid": False,
    }

    try:
        table_result = client.query(
            f"SHOW TABLES FROM {DATABASE_NAME}"
        )

        existing_tables = {
            row[0] for row in table_result.result_rows
        }

        for table_name, required_columns in REQUIRED_TABLES.items():

            if table_name not in existing_tables:
                report["missing_tables"].append(table_name)
                report["tables"][table_name] = {
                    "exists": False,
                    "columns_valid": False,
                    "row_count": 0,
                }
                continue

            description = client.query(
                f"DESCRIBE TABLE {DATABASE_NAME}.{table_name}"
            )

            actual_columns = {
                row[0] for row in description.result_rows
            }

            missing = [
                column
                for column in required_columns
                if column not in actual_columns
            ]

            count_result = client.query(
                f"SELECT count() FROM "
                f"{DATABASE_NAME}.{table_name}"
            )

            row_count = int(count_result.result_rows[0][0])

            report["tables"][table_name] = {
                "exists": True,
                "columns_valid": not missing,
                "row_count": row_count,
            }

            report["total_records"] += row_count

            if missing:
                report["missing_columns"][table_name] = missing

        report["overall_valid"] = (
            not report["missing_tables"]
            and not report["missing_columns"]
            and all(
                table["exists"] and table["columns_valid"]
                for table in report["tables"].values()
            )
        )

    except Exception as exc:
        logger.exception("Database validation failed.")
        report["error"] = str(exc)
        report["overall_valid"] = False

    return report


def check_duplicate_events(client=None):
    """Find duplicate event IDs without deleting any records."""
    try:
        client = _get_client(client)

        result = client.query(
            """
            SELECT event_id, count() AS occurrences
            FROM cognistream.developer_events
            GROUP BY event_id
            HAVING occurrences > 1
            ORDER BY occurrences DESC
            LIMIT 100
            """
        )

        duplicates = [
            {
                "event_id": row[0],
                "occurrences": row[1],
            }
            for row in result.result_rows
        ]

        return {
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "has_duplicates": bool(duplicates),
        }

    except Exception as exc:
        logger.exception("Duplicate event check failed.")
        return {
            "duplicate_count": 0,
            "duplicates": [],
            "has_duplicates": False,
            "error": str(exc),
        }


def check_negative_durations(client=None):
    """Find negative durations in sessions and flow blocks."""
    try:
        client = _get_client(client)

        sessions_result = client.query(
            """
            SELECT count()
            FROM cognistream.developer_sessions
            WHERE duration_minutes < 0
            """
        )

        blocks_result = client.query(
            """
            SELECT count()
            FROM cognistream.flow_blocks
            WHERE duration_minutes < 0
            """
        )

        sessions_count = int(
            sessions_result.result_rows[0][0]
        )

        blocks_count = int(
            blocks_result.result_rows[0][0]
        )

        return {
            "negative_session_durations": sessions_count,
            "negative_flow_block_durations": blocks_count,
            "total_negative_durations": (
                sessions_count + blocks_count
            ),
            "has_negative_durations": bool(
                sessions_count or blocks_count
            ),
        }

    except Exception as exc:
        logger.exception("Negative duration check failed.")
        return {
            "negative_session_durations": 0,
            "negative_flow_block_durations": 0,
            "total_negative_durations": 0,
            "has_negative_durations": False,
            "error": str(exc),
        }
