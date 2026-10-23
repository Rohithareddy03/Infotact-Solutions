"""Calculate developer activity metrics using Polars."""

import polars as pl


REQUIRED_COLUMNS = [
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
]


def calculate_developer_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate activity metrics for each developer.

    Args:
        df: A Polars DataFrame containing validated developer events.

    Returns:
        A DataFrame containing one row per developer.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame.")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.is_empty():
        return pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "total_events": pl.UInt32,
                "active_sources": pl.UInt32,
                "event_types": pl.UInt32,
                "first_activity": pl.String,
                "last_activity": pl.String,
                "activity_span_minutes": pl.Float64,
            }
        )

    # Ensure timestamps have a consistent datetime representation.
    timestamp_dtype = df.schema["event_timestamp"]

    if timestamp_dtype == pl.String:
        df = df.with_columns(
            pl.col("event_timestamp").str.to_datetime(
                time_zone="UTC",
                strict=True,
            )
        )
    elif timestamp_dtype == pl.Datetime:
        if df.schema["event_timestamp"].time_zone is None:
            df = df.with_columns(
                pl.col("event_timestamp").dt.replace_time_zone("UTC")
            )
        else:
            df = df.with_columns(
                pl.col("event_timestamp").dt.convert_time_zone("UTC")
            )
    else:
        raise TypeError(
            "event_timestamp must contain strings or datetime values."
        )

    metrics = (
        df.group_by("developer_id")
        .agg(
            pl.len().alias("total_events"),
            pl.col("source").n_unique().alias("active_sources"),
            pl.col("event_type").n_unique().alias("event_types"),
            pl.col("event_timestamp").min().alias("first_activity"),
            pl.col("event_timestamp").max().alias("last_activity"),
        )
        .with_columns(
            (
                (
                    pl.col("last_activity")
                    - pl.col("first_activity")
                ).dt.total_seconds() / 60
            ).alias("activity_span_minutes"),
            pl.col("first_activity")
            .dt.strftime("%Y-%m-%dT%H:%M:%S%:z")
            .alias("first_activity"),
            pl.col("last_activity")
            .dt.strftime("%Y-%m-%dT%H:%M:%S%:z")
            .alias("last_activity"),
        )
        .sort("developer_id")
    )

    return metrics