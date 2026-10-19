"""Orchestrate developer event loading and validation."""

import logging
from pathlib import Path

from src.ingestion.file_loader import load_events
from src.ingestion.validation import validate_event

logger = logging.getLogger(__name__)


def process_event_file(
    file_path: str | Path,
) -> tuple[list[dict], list[dict]]:
    """Load events and separate valid events from invalid events.

    Returns:
        A tuple containing valid events and invalid-event records.
        Each invalid-event record contains the event and its error reason.
    """
    logger.info("Starting ingestion pipeline: %s", file_path)

    events = load_events(file_path)
    valid_events = []
    invalid_events = []

    for event in events:
        is_valid, reason = validate_event(event)

        if is_valid:
            valid_events.append(event)
        else:
            invalid_events.append({
                "event": event,
                "reason": reason,
            })
            logger.warning(
                "Rejected event %s: %s",
                event.get("event_id", "unknown"),
                reason,
            )

    logger.info(
        "Ingestion completed: total=%d, valid=%d, invalid=%d",
        len(events),
        len(valid_events),
        len(invalid_events),
    )

    return valid_events, invalid_events
