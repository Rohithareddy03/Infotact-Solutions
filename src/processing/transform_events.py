
"""Transform validated developer activity events into Polars data."""

import json
from datetime import date, datetime, timezone
from pathlib import Path

import polars as pl


REQUIRED_COLUMNS = [
    "event_id",
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
    "metadata",
]


def transform_events(events: list[dict]) -> pl.DataFrame:
    """Convert validated events into a normalized Polars DataFrame.

    Timestamps are normalized to UTC. Metadata dictionaries are
    serialized to JSON strings to simplify downstream storage.
    """
    if not isinstance(events, list):
        raise ValueError("Events must be provided as a list.")

    rows = []

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"Event at index {index} must be a dictionary.")

        missing = [
            column for column in REQUIRED_COLUMNS
            if column not in event
        ]
        if missing:
            raise ValueError(
                f"Event at index {index} is missing fields: {missing}"
            )

        timestamp_value = event["event_timestamp"]

        if not isinstance(timestamp_value, str):
            raise ValueError(
                f"Event at index {index} has a non-string timestamp."
            )

        try:
            timestamp = datetime.fromisoformat(
                timestamp_value.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                f"Event at index {index} has an invalid timestamp."
            ) from exc

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError(
                f"Event at index {index} must have a timezone-aware timestamp."
            )

        metadata = event["metadata"]
        if not isinstance(metadata, dict):
            raise ValueError(
                f"Event at index {index} metadata must be a dictionary."
            )

        rows.append({
            "event_id": str(event["event_id"]),
            "developer_id": str(event["developer_id"]),
            "source": str(event["source"]).strip().lower(),
            "event_type": str(event["event_type"]).strip().lower(),
            "event_timestamp": timestamp.astimezone(timezone.utc),
            "metadata": json.dumps(metadata, sort_keys=True),
        })

    schema = {
        "event_id": pl.String,
        "developer_id": pl.String,
        "source": pl.String,
        "event_type": pl.String,
        "event_timestamp": pl.Datetime(time_zone="UTC"),
        "metadata": pl.String,
    }

    if not rows:
        return pl.DataFrame(schema=schema)

    df = pl.DataFrame(rows, schema=schema)

    return df.with_columns([
        pl.col("event_timestamp").dt.date().alias("event_date"),
        pl.col("event_timestamp").dt.hour().alias("event_hour"),
    ])
