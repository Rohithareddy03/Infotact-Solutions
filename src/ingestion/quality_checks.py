"""Data quality checks for CogniStream ingestion events."""

from datetime import datetime


REQUIRED_FIELDS = {
    "event_id",
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
    "metadata",
}

ALLOWED_SOURCES = {
    "github",
    "jira",
    "slack",
    "activitywatch",
}


def validate_event_schema(event: dict) -> tuple[bool, list[str]]:
    """Validate required fields and basic event structure."""

    errors = []

    if not isinstance(event, dict):
        return False, ["Event must be a dictionary."]

    missing_fields = REQUIRED_FIELDS - set(event.keys())

    if missing_fields:
        errors.append(
            "Missing fields: " + ", ".join(sorted(missing_fields))
        )

    if "event_id" in event:
        if not isinstance(event["event_id"], str):
            errors.append("event_id must be a string.")
        elif not event["event_id"].strip():
            errors.append("event_id cannot be empty.")

    if "developer_id" in event:
        if not isinstance(event["developer_id"], str):
            errors.append("developer_id must be a string.")
        elif not event["developer_id"].strip():
            errors.append("developer_id cannot be empty.")

    if "source" in event:
        if not isinstance(event["source"], str):
            errors.append("source must be a string.")
        elif event["source"].strip().lower() not in ALLOWED_SOURCES:
            errors.append("Unsupported event source.")

    if "event_type" in event:
        if (
            not isinstance(event["event_type"], str)
            or not event["event_type"].strip()
        ):
            errors.append("event_type must be a non-empty string.")

    if "metadata" in event:
        if not isinstance(event["metadata"], dict):
            errors.append("metadata must be a dictionary.")

    return len(errors) == 0, errors


def validate_event_timestamp(event: dict) -> tuple[bool, str]:
    """Validate a timezone-aware ISO timestamp."""

    value = event.get("event_timestamp")

    if not isinstance(value, str):
        return False, "event_timestamp must be an ISO timestamp string."

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False, "Invalid event_timestamp format."

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return False, "event_timestamp must include a timezone."

    return True, "Valid timestamp."


def validate_event_batch(events: list[dict]) -> dict:
    """Validate events, normalize sources, and report duplicates."""

    if not isinstance(events, list):
        raise TypeError("events must be a list.")

    valid_events = []
    invalid_events = []
    duplicate_events = []
    duplicate_ids = set()
    seen_ids = set()

    for index, event in enumerate(events):
        schema_valid, schema_errors = validate_event_schema(event)

        if not schema_valid:
            invalid_events.append({
                "index": index,
                "event": event,
                "errors": schema_errors,
            })
            continue

        timestamp_valid, timestamp_message = validate_event_timestamp(event)

        if not timestamp_valid:
            invalid_events.append({
                "index": index,
                "event": event,
                "errors": [timestamp_message],
            })
            continue

        event_id = event["event_id"]

        if event_id in seen_ids:
            duplicate_ids.add(event_id)
            duplicate_events.append({
                "index": index,
                "event_id": event_id,
                "errors": ["Duplicate event_id."],
            })
            continue

        normalized_event = event.copy()
        normalized_event["source"] = event["source"].strip().lower()

        seen_ids.add(event_id)
        valid_events.append(normalized_event)

    return {
        "total_events": len(events),
        "valid_events": valid_events,
        "invalid_events": invalid_events,
        "duplicate_event_ids": sorted(duplicate_ids),
        "duplicate_events": duplicate_events,
        "duplicate_extra_rows": len(duplicate_events),
        "accepted_events": len(valid_events),
        "rejected_events": len(invalid_events) + len(duplicate_events),
    }
