"""Analyze developer context switches using Polars."""

import polars as pl


REQUIRED_COLUMNS = [
    "developer_id",
    "source",
    "event_timestamp",
]


def analyze_context_switches(
    df: pl.DataFrame,
) -> pl.DataFrame:
    """Calculate source switches and elapsed time between events.

    Events are ordered by timestamp separately for each developer.
    A context switch occurs when consecutive events use different
    sources.

    Returns one row per developer.
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
                "context_switches": pl.UInt32,
                "switch_rate_pct": pl.Float64,
                "average_gap_minutes": pl.Float64,
            }
        )

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

    # Sort activities chronologically within each developer.
    ordered = df.sort(["developer_id", "event_timestamp"])

    # Compare each source with the preceding source for that developer.
    ordered = ordered.with_columns(
        pl.col("source")
        .shift(1)
        .over("developer_id")
        .alias("previous_source"),
        pl.col("event_timestamp")
        .shift(1)
        .over("developer_id")
        .alias("previous_timestamp"),
    )

    ordered = ordered.with_columns(
        (
            pl.col("source") != pl.col("previous_source")
        )
        .fill_null(False)
        .alias("is_context_switch"),
        (
            (
                pl.col("event_timestamp")
                - pl.col("previous_timestamp")
            ).dt.total_seconds() / 60
        ).alias("gap_minutes"),
    )

    result = (
        ordered.group_by("developer_id")
        .agg(
            pl.len().alias("total_events"),
            pl.col("is_context_switch")
            .sum()
            .alias("context_switches"),
            pl.col("gap_minutes")
            .mean()
            .alias("average_gap_minutes"),
        )
        .with_columns(
            pl.when(pl.col("total_events") > 1)
            .then(
                pl.col("context_switches")
                / (pl.col("total_events") - 1)
                * 100
            )
            .otherwise(0.0)
            .alias("switch_rate_pct")
        )
        .sort("developer_id")
    )

    return result