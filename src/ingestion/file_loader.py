
"""Load simulated developer activity events from a JSON file."""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_events(file_path: str | Path) -> list[dict]:
    """Load a JSON array of developer events from disk.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the JSON is invalid or has an unexpected structure.
    """
    path = Path(file_path)
    logger.info("Starting event file ingestion: %s", path)

    try:
        with path.open("r", encoding="utf-8") as file:
            events = json.load(file)
    except FileNotFoundError:
        logger.error("Event file not found: %s", path)
        raise
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
        raise ValueError(f"Invalid JSON file: {path}") from exc
    except OSError:
        logger.exception("Could not read event file: %s", path)
        raise

    if not isinstance(events, list):
        logger.error("Expected a JSON array in %s", path)
        raise ValueError("Event file must contain a JSON array.")

    if any(not isinstance(event, dict) for event in events):
        logger.error("File contains a non-object event: %s", path)
        raise ValueError("Every event must be a JSON object.")

    logger.info("Loaded %d events from %s", len(events), path)
    return events
