import polars as pl

DEFAULT_MAX_GAP_MINUTES = 10
DEFAULT_MIN_BLOCK_MINUTES = 15

CODING_EVENT_TYPES = {"coding", "ide_activity"}


def detect_flow_blocks(
    df: pl.DataFrame,
    max_gap_minutes: int = DEFAULT_MAX_GAP_MINUTES,
    min_block_minutes: int = DEFAULT_MIN_BLOCK_MINUTES,
):
    """Detect uninterrupted coding activity blocks."""

    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame")

    if max_gap_minutes < 0 or min_block_minutes < 0:
        raise ValueError("Thresholds cannot be negative")

    required = {
        "event_id", "developer_id", "source",
        "event_type", "event_timestamp"
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    block_schema = {
        "block_id": pl.String,
        "developer_id": pl.String,
        "start_time": df.schema["event_timestamp"],
        "end_time": df.schema["event_timestamp"],
        "event_count": pl.Int64,
        "duration_minutes": pl.Float64,
        "is_qualifying": pl.Boolean,
    }

    if df.is_empty():
        return (
            pl.DataFrame(schema=block_schema),
            df.with_columns(pl.lit(None, dtype=pl.String).alias("block_id"))
        )

    rows = df.sort(
        ["developer_id", "event_timestamp"]
    ).to_dicts()

    blocks = []
    assignments = []
    current_events = []
    current_developer = None

    def save_block():
        nonlocal current_events

        if not current_events:
            return

        start = current_events[0]["event_timestamp"]
        end = current_events[-1]["event_timestamp"]
        duration = (end - start).total_seconds() / 60

        number = sum(
            1 for b in blocks
            if b["developer_id"] == current_developer
        ) + 1

        block_id = f"{current_developer}_BLOCK_{number:03d}"

        blocks.append({
            "block_id": block_id,
            "developer_id": current_developer,
            "start_time": start,
            "end_time": end,
            "event_count": len(current_events),
            "duration_minutes": float(duration),
            "is_qualifying": duration >= min_block_minutes,
        })

        for event in current_events:
            assignments.append({**event, "block_id": block_id})

        current_events = []

    for event in rows:
        developer = event["developer_id"]

        if developer != current_developer:
            save_block()
            current_developer = developer

        is_coding = (
            str(event["source"]).lower() == "activitywatch"
            and str(event["event_type"]).lower() in CODING_EVENT_TYPES
        )

        if not is_coding:
            save_block()
            continue

        if current_events:
            previous = current_events[-1]["event_timestamp"]
            gap = (event["event_timestamp"] - previous).total_seconds()

            if gap > max_gap_minutes * 60:
                save_block()

        current_events.append(event)

    save_block()

    blocks_df = pl.DataFrame(blocks, schema=block_schema)

    event_blocks_df = (
        pl.DataFrame(assignments)
        if assignments
        else df.head(0).with_columns(
            pl.lit(None, dtype=pl.String).alias("block_id")
        )
    )

    return blocks_df, event_blocks_df


def calculate_flow_summary(blocks_df: pl.DataFrame):
    """Calculate developer-level flow activity metrics."""

    if not isinstance(blocks_df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame")

    required = {
        "developer_id", "duration_minutes", "is_qualifying"
    }

    missing = required - set(blocks_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if blocks_df.is_empty():
        return pl.DataFrame(schema={
            "developer_id": pl.String,
            "total_blocks": pl.UInt32,
            "qualifying_blocks": pl.UInt32,
            "estimated_flow_minutes": pl.Float64,
        })

    return (
        blocks_df.group_by("developer_id")
        .agg(
            pl.len().alias("total_blocks"),
            pl.col("is_qualifying").cast(pl.UInt32)
            .sum().alias("qualifying_blocks"),
            pl.when(pl.col("is_qualifying"))
            .then(pl.col("duration_minutes"))
            .otherwise(0.0)
            .sum().alias("estimated_flow_minutes"),
        )
        .sort("developer_id")
    )
