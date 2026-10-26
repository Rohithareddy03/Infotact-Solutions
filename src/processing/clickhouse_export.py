"""Prepare unified developer analytics for ClickHouse insertion."""

from datetime import date, datetime

import polars as pl


COUNT_COLUMNS = [
    "total_events",
    "active_sources",
    "event_types",
    "context_switches",
    "activity_block_count",
    "total_block_events",
]

FLOAT_COLUMNS = [
    "switch_rate_pct",
    "average_gap_minutes",
    "average_block_duration_minutes",
    "longest_block_duration_minutes",
]

TIMESTAMP_COLUMNS = [
    "first_activity",
    "last_activity",
]


def prepare_clickhouse_records(
    df: pl.DataFrame,
    snapshot_date: date | str,
) -> list[dict]:
    """Convert unified analytics into ClickHouse-ready records.

    Args:
        df: One row per developer containing unified analytics.
        snapshot_date: Reporting date as a date object or ISO date string.

    Returns:
        A list of dictionaries ready for database insertion.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame.")

    if isinstance(snapshot_date, datetime):
        raise ValueError(
            "snapshot_date must be a date or YYYY-MM-DD string, "
            "not a datetime."
        )

    if isinstance(snapshot_date, str):
        try:
            snapshot_date = date.fromisoformat(snapshot_date)
        except ValueError as exc:
            raise ValueError(
                "snapshot_date must use YYYY-MM-DD format."
            ) from exc

    if not isinstance(snapshot_date, date):
        raise TypeError(
            "snapshot_date must be a date or YYYY-MM-DD string."
        )

    if "developer_id" not in df.columns:
        raise ValueError("Missing required column: developer_id")

    if df.get_column("developer_id").null_count() > 0:
        raise ValueError("developer_id cannot contain null values.")

    if (
        df.get_column("developer_id").cast(pl.String).str.strip_chars()
        .eq("")
        .any()
    ):
        raise ValueError("developer_id cannot be empty.")

    if df.get_column("developer_id").n_unique() != df.height:
        raise ValueError(
            "Input must contain at most one row per developer."
        )

    if df.is_empty():
        return []

    available_columns = set(df.columns)
    records = []

    for row in df.iter_rows(named=True):
        record = {
            "snapshot_date": snapshot_date,
            "developer_id": str(row["developer_id"]),
        }

        # Store absent or null counts as zero.
        for column in COUNT_COLUMNS:
            value = row.get(column)
            if value is None:
                value = 0
            record[column] = int(value)

        # Preserve unknown measurements as None.
        for column in FLOAT_COLUMNS:
            value = row.get(column)
            record[column] = (
                float(value) if value is not None else None
            )

        # Preserve timestamp fields when available.
        for column in TIMESTAMP_COLUMNS:
            value = row.get(column) if column in available_columns else None

            if isinstance(value, datetime):
                value = value.isoformat()

            record[column] = value

        records.append(record)

    return records