import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "event_id",
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
    "metadata",
]


def load_json_events(file_path: str | Path) -> list[dict]:
    """Load developer events from a JSON array."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Event file not found: {path}")

    with path.open("r", encoding="utf-8-sig") as file:
        events = json.load(file)

    if not isinstance(events, list):
        raise ValueError("JSON data must contain a list of events.")

    return events


def normalize_timestamp(value: Any) -> datetime:
    """Convert an ISO timestamp into a timezone-aware UTC datetime."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Missing or invalid event_timestamp")

    try:
        timestamp = datetime.fromisoformat(
            value.strip().replace("Z", "+00:00")
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return timestamp.astimezone(timezone.utc)

    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid event_timestamp: {value}") from exc


def validate_event_records(
    events: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Separate valid events from rejected events."""
    valid_records = []
    rejected_records = []

    for index, event in enumerate(events):
        try:
            if not isinstance(event, dict):
                raise ValueError("Event must be a JSON object")

            missing = [
                column
                for column in REQUIRED_COLUMNS
                if column not in event
            ]

            if missing:
                raise ValueError(
                    f"Missing required columns: {missing}"
                )

            for column in REQUIRED_COLUMNS[:4]:
                if not isinstance(event[column], str) or not event[column].strip():
                    raise ValueError(f"Invalid {column}")

            if not isinstance(event["metadata"], dict):
                raise ValueError("Metadata must be a JSON object")

            cleaned_event = {
                "event_id": event["event_id"].strip(),
                "developer_id": event["developer_id"].strip(),
                "source": event["source"].strip(),
                "event_type": event["event_type"].strip(),
                "event_timestamp": normalize_timestamp(
                    event["event_timestamp"]
                ),
                "metadata": json.dumps(
                    event["metadata"],
                    ensure_ascii=False,
                ),
            }

            valid_records.append(cleaned_event)

        except (ValueError, TypeError) as exc:
            rejected_records.append({
                "record": json.dumps(event, default=str),
                "reason": str(exc),
            })

            logger.warning(
                "Rejected event at index %s: %s",
                index,
                exc,
            )

    return valid_records, rejected_records


def events_to_dataframe(events: list[dict]) -> pl.DataFrame:
    """Convert validated events into a structured Polars DataFrame."""
    schema = {
        "event_id": pl.String,
        "developer_id": pl.String,
        "source": pl.String,
        "event_type": pl.String,
        "event_timestamp": pl.Datetime("us", "UTC"),
        "metadata": pl.String,
    }

    if not events:
        return pl.DataFrame(schema=schema)

    return pl.DataFrame(events, schema=schema)


def process_event_file(
    file_path: str | Path,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load, validate and transform a developer event JSON file."""
    events = load_json_events(file_path)

    valid_records, rejected_records = validate_event_records(events)

    clean_df = events_to_dataframe(valid_records)

    rejected_df = pl.DataFrame(
        rejected_records,
        schema={
            "record": pl.String,
            "reason": pl.String,
        },
    )

    logger.info(
        "Processed %s events: %s accepted, %s rejected",
        len(events),
        len(valid_records),
        len(rejected_records),
    )

    return clean_df, rejected_df