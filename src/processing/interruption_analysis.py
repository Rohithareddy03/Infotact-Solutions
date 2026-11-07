import polars as pl

DEFAULT_INTERRUPTION_WINDOW_MINUTES = 5

CODING_SOURCES = {"activitywatch"}
CODING_EVENT_TYPES = {"coding", "ide_activity"}

INTERRUPTION_SOURCES = {"slack"}
INTERRUPTION_EVENT_TYPES = {"message", "notification"}


def detect_potential_interruptions(
    df: pl.DataFrame,
    window_minutes: int = DEFAULT_INTERRUPTION_WINDOW_MINUTES,
):
    """
    Identify potential Slack interruptions occurring within
    the configured time window after coding events.

    Each coding event and Slack event can be matched only once.

    Returns:
        interruptions_df: matched potential interruptions
        coding_events_df: coding events with match status

    These matches are activity-based candidates, not proof
    of actual developer interruption.
    """

    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame")

    if window_minutes <= 0:
        raise ValueError(
            "Interruption window must be greater than zero"
        )

    required_columns = [
        "event_id",
        "developer_id",
        "source",
        "event_type",
        "event_timestamp",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    timestamp_dtype = df.schema["event_timestamp"]

    interruption_schema = {
        "developer_id": pl.String,
        "coding_event_id": pl.String,
        "interruption_event_id": pl.String,
        "coding_timestamp": timestamp_dtype,
        "interruption_timestamp": timestamp_dtype,
        "delay_minutes": pl.Float64,
        "interruption_source": pl.String,
        "interruption_type": pl.String,
    }

    coding_schema = {
        **df.schema,
        "is_matched": pl.Boolean,
        "matched_interruption_event_id": pl.String,
    }

    if df.is_empty():
        return (
            pl.DataFrame(schema=interruption_schema),
            df.with_columns([
                pl.lit(False).alias("is_matched"),
                pl.lit(None, dtype=pl.String).alias(
                    "matched_interruption_event_id"
                ),
            ]),
        )

    rows = df.sort(
        ["developer_id", "event_timestamp", "event_id"]
    ).to_dicts()

    developers = {}

    for row in rows:
        developers.setdefault(row["developer_id"], []).append(row)

    interruptions = []
    coding_results = []

    window_seconds = window_minutes * 60

    for developer_id, events in developers.items():

        coding_events = [
            event for event in events
            if str(event["source"]).lower() in CODING_SOURCES
            and str(event["event_type"]).lower() in CODING_EVENT_TYPES
        ]

        slack_events = [
            event for event in events
            if str(event["source"]).lower() in INTERRUPTION_SOURCES
            and str(event["event_type"]).lower()
            in INTERRUPTION_EVENT_TYPES
        ]

        matched_coding_ids = set()
        matched_slack_ids = set()
        matches_by_coding = {}

        for slack in slack_events:

            eligible = []

            for coding in coding_events:

                if coding["event_id"] in matched_coding_ids:
                    continue

                delay = (
                    slack["event_timestamp"]
                    - coding["event_timestamp"]
                ).total_seconds()

                if 0 <= delay <= window_seconds:
                    eligible.append((coding, delay))

            if not eligible:
                continue

            # Match the Slack event to the most recent
            # eligible, unmatched coding event.
            coding, delay = max(
                eligible,
                key=lambda item: (
                    item[0]["event_timestamp"],
                    item[0]["event_id"],
                ),
            )

            matched_coding_ids.add(coding["event_id"])
            matched_slack_ids.add(slack["event_id"])

            matches_by_coding[coding["event_id"]] = slack["event_id"]

            interruptions.append({
                "developer_id": developer_id,
                "coding_event_id": coding["event_id"],
                "interruption_event_id": slack["event_id"],
                "coding_timestamp": coding["event_timestamp"],
                "interruption_timestamp": slack["event_timestamp"],
                "delay_minutes": delay / 60,
                "interruption_source": slack["source"],
                "interruption_type": slack["event_type"],
            })

        for coding in coding_events:
            coding_results.append({
                **coding,
                "is_matched": (
                    coding["event_id"] in matched_coding_ids
                ),
                "matched_interruption_event_id": (
                    matches_by_coding.get(coding["event_id"])
                ),
            })

    interruptions_df = pl.DataFrame(
        interruptions,
        schema=interruption_schema,
    )

    coding_events_df = (
        pl.DataFrame(coding_results, schema=coding_schema)
        if coding_results
        else pl.DataFrame(schema=coding_schema)
    )

    return interruptions_df, coding_events_df


def calculate_interruption_summary(
    interruptions_df: pl.DataFrame,
    coding_events_df: pl.DataFrame,
):
    """
    Calculate developer-level interruption statistics.

    Interruption rate =
        potential interruptions / coding events * 100
    """

    if not isinstance(interruptions_df, pl.DataFrame):
        raise TypeError(
            "interruptions_df must be a Polars DataFrame"
        )

    if not isinstance(coding_events_df, pl.DataFrame):
        raise TypeError(
            "coding_events_df must be a Polars DataFrame"
        )

    for column in ["developer_id"]:
        if column not in interruptions_df.columns:
            raise ValueError(
                f"Missing column in interruptions_df: {column}"
            )

        if column not in coding_events_df.columns:
            raise ValueError(
                f"Missing column in coding_events_df: {column}"
            )

    summary_schema = {
        "developer_id": pl.String,
        "total_coding_events": pl.UInt32,
        "potential_interruptions": pl.UInt32,
        "interruption_rate_percent": pl.Float64,
    }

    if coding_events_df.is_empty():
        return pl.DataFrame(schema=summary_schema)

    coding_summary = (
        coding_events_df
        .group_by("developer_id")
        .agg(
            pl.len().alias("total_coding_events")
        )
    )

    interruption_summary = (
        interruptions_df
        .group_by("developer_id")
        .agg(
            pl.len().alias("potential_interruptions")
        )
    )

    return (
        coding_summary
        .join(
            interruption_summary,
            on="developer_id",
            how="left",
        )
        .with_columns(
            pl.col("potential_interruptions")
            .fill_null(0)
            .cast(pl.UInt32)
        )
        .with_columns(
            (
                pl.col("potential_interruptions")
                / pl.col("total_coding_events")
                * 100
            )
            .alias("interruption_rate_percent")
        )
        .select(list(summary_schema.keys()))
        .sort("developer_id")
    )
