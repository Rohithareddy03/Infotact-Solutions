"""Orchestrate developer event loading and validation."""

import logging
import time
from pathlib import Path

from src.ingestion.file_loader import load_events
from src.ingestion.validation import validate_event

logger = logging.getLogger(__name__)


def load_events_with_retry(
    file_path: str | Path,
    max_attempts: int = 3,
    retry_delay: float = 1.0,
) -> list[dict]:
    """Load events again when a temporary file-access error occurs.

    FileNotFoundError and ValueError are treated as permanent input errors
    and are not retried.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    if retry_delay < 0:
        raise ValueError("retry_delay cannot be negative.")

    for attempt in range(1, max_attempts + 1):
        try:
            return load_events(file_path)

        except (FileNotFoundError, ValueError):
            logger.error(
                "Permanent ingestion error for %s; retry skipped.",
                file_path,
            )
            raise

        except OSError:
            logger.exception(
                "Temporary file-access failure: attempt %d of %d for %s",
                attempt,
                max_attempts,
                file_path,
            )

            if attempt == max_attempts:
                logger.error(
                    "All %d ingestion attempts failed for %s.",
                    max_attempts,
                    file_path,
                )
                raise

            if retry_delay > 0:
                time.sleep(retry_delay)

    raise RuntimeError("Unexpected ingestion retry state.")


def process_event_file(
    file_path: str | Path,
    max_attempts: int = 3,
    retry_delay: float = 1.0,
) -> tuple[list[dict], list[dict]]:
    """Load events and separate valid events from invalid events.

    Returns:
        A tuple containing valid events and invalid-event records.
        Each invalid-event record contains the event and its error reason.
    """
    logger.info("Starting ingestion pipeline: %s", file_path)

    events = load_events_with_retry(
        file_path,
        max_attempts=max_attempts,
        retry_delay=retry_delay,
    )

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