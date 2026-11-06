
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ClickHouseConnectionError(Exception):
    """Raised when ClickHouse operations fail."""


def create_clickhouse_client():
    """Create a ClickHouse client using environment variables."""

    host = os.getenv("CLICKHOUSE_HOST", "localhost")
    port = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    username = os.getenv("CLICKHOUSE_USER", "default")
    password = os.getenv("CLICKHOUSE_PASSWORD", "")
    database = os.getenv("CLICKHOUSE_DATABASE", "cognistream")

    try:
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

        logger.info("ClickHouse client created successfully.")
        return client

    except Exception as exc:
        logger.exception("Failed to create ClickHouse client.")
        raise ClickHouseConnectionError(
            "Unable to connect to ClickHouse."
        ) from exc


def check_connection(client: Any) -> bool:
    """Check ClickHouse connectivity."""

    try:
        return bool(client.ping())

    except Exception:
        logger.exception("Connection check failed.")
        return False


def insert_developer_events(client: Any, events: list[dict]) -> int:
    """Validate and insert developer activity events."""

    if not isinstance(events, list) or not events:
        raise ValueError("Events must be a non-empty list.")

    column_names = [
        "developer_id",
        "event_type",
        "event_timestamp",
        "metadata",
    ]

    rows = []

    for event in events:

        if not isinstance(event, dict):
            raise ValueError("Each event must be a dictionary.")

        for field in (
            "developer_id",
            "event_type",
            "event_timestamp",
        ):
            if field not in event or event[field] is None:
                raise ValueError(f"Missing required field: {field}")

        timestamp = event["event_timestamp"]

        if not isinstance(timestamp, datetime):
            raise ValueError("event_timestamp must be a datetime.")

        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Timestamp must be timezone-aware.")

        if timestamp.utcoffset().total_seconds() != 0:
            raise ValueError("Timestamp must be in UTC.")

        metadata = event.get("metadata", {})

        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary.")

        rows.append([
            event["developer_id"],
            event["event_type"],
            timestamp.astimezone(timezone.utc),
            json.dumps(metadata),
        ])

    try:
        client.insert(
            "developer_events",
            rows,
            column_names=column_names,
        )

        logger.info("Inserted %s events successfully.", len(rows))
        return len(rows)

    except Exception as exc:
        logger.exception("Event insertion failed.")
        raise ClickHouseConnectionError(
            "Unable to insert developer events."
        ) from exc
