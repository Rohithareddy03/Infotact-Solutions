import polars as pl

DEFAULT_IDLE_THRESHOLD_MINUTES = 30


def analyze_context_switches(
    df: pl.DataFrame,
    idle_threshold_minutes: int = DEFAULT_IDLE_THRESHOLD_MINUTES,
):
    """Analyze transitions between developer activity sources."""

    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame")

    if idle_threshold_minutes <= 0:
        raise ValueError("Idle threshold must be greater than zero")

    required_columns = [
        "developer_id",
        "source",
        "event_timestamp",
    ]

    missing = [
        col for col in required_columns if col not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    summary_schema = {
        "developer_id": df.schema["developer_id"],
        "total_events": pl.UInt32,
        "total_adjacent_pairs": pl.UInt32,
        "total_switches": pl.UInt32,
        "switch_rate": pl.Float64,
    }

    transition_schema = {
        "developer_id": df.schema["developer_id"],
        "previous_source": df.schema["source"],
        "current_source": df.schema["source"],
        "previous_timestamp": df.schema["event_timestamp"],
        "current_timestamp": df.schema["event_timestamp"],
        "gap_minutes": pl.Float64,
    }

    if df.is_empty():
        return (
            pl.DataFrame(schema=summary_schema),
            pl.DataFrame(schema=transition_schema),
        )

    if df["developer_id"].null_count() > 0:
        raise ValueError("developer_id cannot contain null values")

    if df["source"].null_count() > 0:
        raise ValueError("source cannot contain null values")

    if df["event_timestamp"].null_count() > 0:
        raise ValueError("event_timestamp cannot contain null values")

    sorted_df = df.sort(["developer_id", "event_timestamp"])

    previous_df = sorted_df.with_columns([
        pl.col("source").shift(1).over("developer_id")
        .alias("previous_source"),

        pl.col("event_timestamp").shift(1).over("developer_id")
        .alias("previous_timestamp"),
    ])

    candidates = (
        previous_df
        .filter(pl.col("previous_source").is_not_null())
        .with_columns(
            (
                (
                    pl.col("event_timestamp")
                    - pl.col("previous_timestamp")
                ).dt.total_seconds() / 60
            ).alias("gap_minutes")
        )
    )

    valid_pairs = candidates.filter(
        pl.col("gap_minutes") <= idle_threshold_minutes
    )

    transitions_df = (
        valid_pairs
        .filter(pl.col("source") != pl.col("previous_source"))
        .select([
            "developer_id",
            "previous_source",
            pl.col("source").alias("current_source"),
            "previous_timestamp",
            pl.col("event_timestamp").alias("current_timestamp"),
            "gap_minutes",
        ])
    )

    event_counts = (
        sorted_df.group_by("developer_id")
        .agg(
            pl.len().cast(pl.UInt32).alias("total_events")
        )
    )

    pair_counts = (
        valid_pairs.group_by("developer_id")
        .agg(
            pl.len().cast(pl.UInt32).alias("total_adjacent_pairs")
        )
    )

    switch_counts = (
        transitions_df.group_by("developer_id")
        .agg(
            pl.len().cast(pl.UInt32).alias("total_switches")
        )
    )

    summary_df = (
        event_counts
        .join(pair_counts, on="developer_id", how="left")
        .join(switch_counts, on="developer_id", how="left")
        .with_columns([
            pl.col("total_adjacent_pairs").fill_null(0),
            pl.col("total_switches").fill_null(0),
        ])
        .with_columns(
            pl.when(pl.col("total_adjacent_pairs") > 0)
            .then(
                pl.col("total_switches")
                / pl.col("total_adjacent_pairs")
            )
            .otherwise(0.0)
            .cast(pl.Float64)
            .alias("switch_rate")
        )
        .sort("developer_id")
    )

    return summary_df, transitions_df
