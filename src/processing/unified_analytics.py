"""Combine CogniStream developer analytics into one dataset."""

import polars as pl


def build_unified_analytics(
    activity_metrics: pl.DataFrame,
    context_metrics: pl.DataFrame,
    activity_blocks: pl.DataFrame,
) -> pl.DataFrame:
    """Combine developer activity, context switches, and activity blocks.

    Each input must contain a developer_id column.
    Each developer must appear at most once in the first two datasets.
    Activity blocks may contain multiple rows per developer.

    Returns:
        One row per developer with combined analytics.
    """
    inputs = {
        "activity_metrics": activity_metrics,
        "context_metrics": context_metrics,
        "activity_blocks": activity_blocks,
    }

    for name, df in inputs.items():
        if not isinstance(df, pl.DataFrame):
            raise TypeError(f"{name} must be a Polars DataFrame.")

        if "developer_id" not in df.columns:
            raise ValueError(
                f"{name} is missing the developer_id column."
            )

    for name, df in (
        ("activity_metrics", activity_metrics),
        ("context_metrics", context_metrics),
    ):
        if df.get_column("developer_id").n_unique() != df.height:
            raise ValueError(
                f"{name} must contain at most one row per developer."
            )

    # Aggregate activity-block data to developer level.
    if activity_blocks.is_empty():
        block_summary = pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "activity_block_count": pl.UInt32,
                "total_block_events": pl.UInt32,
                "average_block_duration_minutes": pl.Float64,
                "longest_block_duration_minutes": pl.Float64,
            }
        )
    else:
        required_block_columns = {
            "event_count",
            "duration_minutes",
        }
        missing = required_block_columns - set(activity_blocks.columns)

        if missing:
            raise ValueError(
                f"activity_blocks is missing columns: {sorted(missing)}"
            )

        block_summary = (
            activity_blocks
            .group_by("developer_id")
            .agg(
                pl.len().alias("activity_block_count"),
                pl.col("event_count")
                .sum()
                .alias("total_block_events"),
                pl.col("duration_minutes")
                .mean()
                .alias("average_block_duration_minutes"),
                pl.col("duration_minutes")
                .max()
                .alias("longest_block_duration_minutes"),
            )
        )

    # Use full joins so developers present in any input are retained.
    result = activity_metrics.join(
        context_metrics,
        on="developer_id",
        how="full",
        coalesce=True,
    )

    result = result.join(
        block_summary,
        on="developer_id",
        how="full",
        coalesce=True,
    )

    # Replace missing count metrics with zero.
    count_columns = [
        "total_events",
        "active_sources",
        "event_types",
        "context_switches",
        "activity_block_count",
        "total_block_events",
    ]

    available_count_columns = [
        column for column in count_columns
        if column in result.columns
    ]

    if available_count_columns:
        result = result.with_columns(
            [
                pl.col(column).fill_null(0)
                for column in available_count_columns
            ]
        )

    return result.sort("developer_id")