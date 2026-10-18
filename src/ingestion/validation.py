import datetime

ALLOWED_SOURCES = {
    "github",
    "jira",
    "slack",
    "activitywatch",
}

REQUIRED_FIELDS = {
    "event_id",
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
    "metadata",
}


def validate_event(event: dict) -> tuple[bool, str]:
    """Validate one normalized developer activity event."""

    if not isinstance(event, dict):
        return False, "Event must be a dictionary"

    missing = REQUIRED_FIELDS - event.keys()
    if missing:
        return False, f"Missing fields: {', '.join(sorted(missing))}"

    for field in (
        "event_id",
        "developer_id",
        "source",
        "event_type",
        "event_timestamp",
    ):
        if not isinstance(event[field], str) or not event[field].strip():
            return False, f"{field} must be a non-empty string"

    if event["source"] not in ALLOWED_SOURCES:
        return False, "Unsupported event source"

    if not isinstance(event["metadata"], dict):
        return False, "metadata must be a dictionary"

    try:
        timestamp = datetime.datetime.fromisoformat(
            event["event_timestamp"].replace("Z", "+00:00")
        )
    except ValueError:
        return False, "Invalid event_timestamp format"

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False, "event_timestamp must include a timezone"

    return True, "Event is valid"


def validate_events(events: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separate valid events from invalid events."""
    valid_events = []
    invalid_events = []

    for event in events:
        is_valid, reason = validate_event(event)

        if is_valid:
            valid_events.append(event)
        else:
            invalid_events.append({
                "event": event,
                "error": reason,
            })

    return valid_events, invalid_events
