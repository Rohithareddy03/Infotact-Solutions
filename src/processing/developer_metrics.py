
import polars as pl


def calculate_developer_metrics(
    events_df: pl.DataFrame,
    sessions_df: pl.DataFrame,
    transitions_df: pl.DataFrame,
) -> pl.DataFrame:
    """
    Calculate developer-level baseline activity metrics.

    Returns:
        A Polars DataFrame containing one row per developer.
    """

    # Validate required columns.
    required_columns = [
        (events_df, ["developer_id", "event_type"], "events"),
        (
            sessions_df,
            [
                "developer_id",
                "duration_minutes",
                "event_count",
            ],
            "sessions",
        ),
        (
            transitions_df,
            ["developer_id"],
            "transitions",
        ),
    ]

    for df, required, name in required_columns:
        missing = [
            col for col in required
            if col not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns in {name}: {missing}"
            )

    # Calculate event metrics.
    event_metrics = (
        events_df
        .group_by("developer_id")
        .agg([
            pl.len().alias("total_events"),
            (
                pl.col("event_type")
                .cast(pl.String)
                .str.to_lowercase()
                .is_in(["commit", "push"])
                .fill_null(False)
                .sum()
            ).alias("total_commits"),
        ])
    )

    # Calculate session metrics.
    session_metrics = (
        sessions_df
        .group_by("developer_id")
        .agg([
            pl.len().alias("total_sessions"),
            pl.col("duration_minutes")
            .sum()
            .alias("estimated_activity_minutes"),
            pl.col("duration_minutes")
            .mean()
            .alias("average_session_minutes"),
            pl.col("event_count")
            .mean()
            .alias("average_events_per_session"),
        ])
    )

    # Calculate context switches.
    switch_metrics = (
        transitions_df
        .group_by("developer_id")
        .agg(
            pl.len().alias("total_context_switches")
        )
    )

    # Combine all metrics.
    result = event_metrics.join(
        session_metrics,
        on="developer_id",
        how="left",
    )

    result = result.join(
        switch_metrics,
        on="developer_id",
        how="left",
    )

    # Replace missing metrics with zero.
    result = result.with_columns([
        pl.col("total_sessions").fill_null(0),
        pl.col("estimated_activity_minutes")
        .fill_null(0.0),
        pl.col("average_session_minutes")
        .fill_null(0.0),
        pl.col("average_events_per_session")
        .fill_null(0.0),
        pl.col("total_context_switches").fill_null(0),
    ])

    return result.sort("developer_id")
