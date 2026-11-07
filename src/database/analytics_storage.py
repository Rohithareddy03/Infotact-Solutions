import polars as pl

from src.database.clickhouse_connection import (
    create_clickhouse_client,
)


TABLE_CONFIG = {
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
        "gap_minutes",
    ],
    "flow_blocks": [
        "developer_id",
        "block_start",
        "block_end",
        "duration_minutes",
        "event_count",
        "qualifies",
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
        "estimated_activity_minutes",
        "average_session_minutes",
        "average_events_per_session",
        "total_context_switches",
        "total_blocks",
        "qualifying_blocks",
        "estimated_flow_minutes",
        "total_coding_events",
        "potential_interruptions",
        "interruption_rate_pct",
    ],
}


def insert_analytics_dataframe(
    client,
    table_name: str,
    dataframe: pl.DataFrame,
) -> int:
    """
    Insert a Polars DataFrame into a ClickHouse analytics table.

    Returns the number of inserted rows.
    """

    if table_name not in TABLE_CONFIG:
        raise ValueError(
            f"Unsupported analytics table: {table_name}"
        )

    if not isinstance(dataframe, pl.DataFrame):
        raise TypeError(
            "dataframe must be a Polars DataFrame"
        )

    required_columns = TABLE_CONFIG[table_name]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns for {table_name}: "
            f"{missing_columns}"
        )

    if dataframe.is_empty():
        return 0

    ordered_dataframe = dataframe.select(required_columns)

    records = ordered_dataframe.rows()

    client.insert(
        table_name,
        records,
        column_names=required_columns,
    )

    return len(records)


def store_analytics_results(
    analytics_results: dict,
    client=None,
) -> dict:
    """
    Store multiple analytics DataFrames in ClickHouse.
    """

    if client is None:
        client = create_clickhouse_client()

    inserted_counts = {}

    for table_name, dataframe in analytics_results.items():
        inserted_counts[table_name] = (
            insert_analytics_dataframe(
                client,
                table_name,
                dataframe,
            )
        )

    return inserted_counts