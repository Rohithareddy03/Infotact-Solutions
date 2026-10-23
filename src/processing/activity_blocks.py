"""Detect uninterrupted developer activity blocks."""

import polars as pl


REQUIRED_COLUMNS = [
    "developer_id",
    "event_timestamp",
]


def detect_activity_blocks(
    df: pl.DataFrame,
    inactivity_threshold_minutes: int = 15,
) -> pl.DataFrame:
    """Group developer events into activity blocks.

    A new block starts when the gap between consecutive events
    for the same developer exceeds the inactivity threshold.

    Args:
        df: Polars DataFrame containing developer activity events.
        inactivity_threshold_minutes: Maximum gap allowed between
            consecutive events in the same activity block.

    Returns:
        A DataFrame containing one row per activity block.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame.")

    if (
        isinstance(inactivity_threshold_minutes, bool)
        or not isinstance(inactivity_threshold_minutes, int)
        or inactivity_threshold_minutes < 0
    ):
        raise ValueError(
            "inactivity_threshold_minutes must be a non-negative integer."
        )

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    output_schema = {
        "developer_id": pl.String,
        "block_number": pl.UInt32,
        "start_time": pl.String,
        "end_time": pl.String,
        "event_count": pl.UInt32,
        "duration_minutes": pl.Float64,
    }

    if df.is_empty():
        return pl.DataFrame(schema=output_schema)

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

    # Sort chronologically within each developer.
    ordered = df.sort(["developer_id", "event_timestamp"])

    # Calculate the gap between consecutive events for each developer.
    ordered = ordered.with_columns(
        pl.col("event_timestamp")
        .shift(1)
        .over("developer_id")
        .alias("previous_timestamp")
    )

    ordered = ordered.with_columns(
        (
            (
                pl.col("event_timestamp")
                - pl.col("previous_timestamp")
            ).dt.total_seconds() / 60
        ).alias("gap_minutes")
    )

    # Start a new block if this is the first event or the gap
    # exceeds the inactivity threshold.
    ordered = ordered.with_columns(
        (
            pl.col("previous_timestamp").is_null()
            | (
                pl.col("gap_minutes")
                > inactivity_threshold_minutes
            )
        )
        .cast(pl.UInt32)
        .alias("new_block")
    )

    # Number the blocks separately for each developer.
    ordered = ordered.with_columns(
        pl.col("new_block")
        .cum_sum()
        .over("developer_id")
        .alias("block_number")
    )

    # Summarize each activity block.
    result = (
        ordered.group_by(["developer_id", "block_number"])
        .agg(
            pl.col("event_timestamp").min().alias("start_time"),
            pl.col("event_timestamp").max().alias("end_time"),
            pl.len().alias("event_count"),
        )
        .with_columns(
            (
                (
                    pl.col("end_time") - pl.col("start_time")
                ).dt.total_seconds() / 60
            ).alias("duration_minutes"),
            pl.col("start_time")
            .dt.strftime("%Y-%m-%dT%H:%M:%S%:z")
            .alias("start_time"),
            pl.col("end_time")
            .dt.strftime("%Y-%m-%dT%H:%M:%S%:z")
            .alias("end_time"),
        )
        .sort(["developer_id", "block_number"])
    )

    return result