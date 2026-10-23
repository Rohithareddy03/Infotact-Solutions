
"""Prepare unified developer analytics for ClickHouse insertion."""

from datetime import datetime
import math

import polars as pl


# Canonical schema for the developer analytics table.
ANALYTICS_COLUMNS = [
    "developer_id",
    "total_events",
    "active_sources",
    "event_types",
    "context_switches",
    "switch_rate_pct",
    "activity_block_count",
    "total_block_events",
    "average_block_duration_minutes",
    "longest_block_duration_minutes",
]

COUNT_COLUMNS = [
    "total_events",
    "active_sources",
    "event_types",
    "context_switches",
    "activity_block_count",
    "total_block_events",
]

METRIC_DEFAULTS = {
    "total_events": 0,
    "active_sources": 0,
    "event_types": 0,
    "context_switches": 0,
    "switch_rate_pct": None,
    "activity_block_count": 0,
    "total_block_events": 0,
    "average_block_duration_minutes": None,
    "longest_block_duration_minutes": None,
}


def prepare_clickhouse_data(
    df: pl.DataFrame,
) -> pl.DataFrame:
    """Validate and normalize analytics for ClickHouse storage.

    Missing optional metrics receive documented defaults.
    Required developer IDs must be non-empty and unique.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame.")

    if "developer_id" not in df.columns:
        raise ValueError("Missing required column: developer_id")

    if df.is_empty():
        return pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "total_events": pl.Int64,
                "active_sources": pl.Int64,
                "event_types": pl.Int64,
                "context_switches": pl.Int64,
                "switch_rate_pct": pl.Float64,
                "activity_block_count": pl.Int64,
                "total_block_events": pl.Int64,
                "average_block_duration_minutes": pl.Float64,
                "longest_block_duration_minutes": pl.Float64,
            }
        )

    if df.get_column("developer_id").null_count() > 0:
        raise ValueError("developer_id cannot contain null values.")

    df = df.with_columns(
        pl.col("developer_id").cast(pl.String).str.strip_chars()
    )

    if (df.get_column("developer_id") == "").any():
        raise ValueError("developer_id cannot be empty.")

    if df.get_column("developer_id").n_unique() != df.height:
        raise ValueError("Each developer_id must be unique.")

    # Add optional metrics using explicit defaults.
    for column, default in METRIC_DEFAULTS.items():
        if column not in df.columns:
            df = df.with_columns(
                pl.lit(default).alias(column)
            )

    # Normalize count fields to non-negative integers.
    for column in COUNT_COLUMNS:
        values = df.get_column(column).to_list()
        normalized = []

        for value in values:
            if value is None:
                value = 0

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
                or not float(value).is_integer()
            ):
                raise ValueError(
                    f"{column} must contain non-negative integers."
                )

            normalized.append(int(value))

        df = df.with_columns(
            pl.Series(column, normalized, dtype=pl.Int64)
        )

    # Normalize percentage and duration fields.
    float_columns = [
        "switch_rate_pct",
        "average_block_duration_minutes",
        "longest_block_duration_minutes",
    ]

    for column in float_columns:
        values = df.get_column(column).to_list()
        normalized = []

        for value in values:
            if value is None:
                normalized.append(None)
                continue

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError(
                    f"{column} must contain non-negative finite numbers "
                    "or null values."
                )

            normalized.append(float(value))

        df = df.with_columns(
            pl.Series(column, normalized, dtype=pl.Float64)
        )

    if (
        df.filter(pl.col("switch_rate_pct") > 100).height > 0
    ):
        raise ValueError("switch_rate_pct cannot exceed 100.")

    if (
        df.filter(
            pl.col("longest_block_duration_minutes")
            < pl.col("average_block_duration_minutes")
        ).height > 0
    ):
        raise ValueError(
            "Longest block duration cannot be less than average duration."
        )

    return df.select(ANALYTICS_COLUMNS).sort("developer_id")


def to_clickhouse_records(
    df: pl.DataFrame,
) -> list[dict]:
    """Convert prepared analytics to ClickHouse-ready dictionaries."""
    prepared = prepare_clickhouse_data(df)

    return [
        {
            column: (
                value.isoformat()
                if isinstance(value, datetime)
                else value
            )
            for column, value in row.items()
        }
        for row in prepared.to_dicts()
    ]
