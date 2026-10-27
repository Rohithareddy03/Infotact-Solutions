"""ClickHouse connection and analytics insertion utilities."""

import logging
import os
from typing import Any

import clickhouse_connect


logger = logging.getLogger(__name__)


def create_clickhouse_client():
    """Create a ClickHouse client using environment configuration."""

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

        logger.info("ClickHouse client created.")
        return client

    except Exception:
        logger.exception("Failed to create ClickHouse client.")
        raise


def insert_developer_analytics(
    client: Any,
    records: list[dict],
) -> int:
    """Insert prepared analytics records into ClickHouse.

    Args:
        client: An initialized ClickHouse client.
        records: Records prepared by clickhouse_export.py.

    Returns:
        Number of records submitted for insertion.

    Raises:
        ValueError: If records are not a list of dictionaries.
        Exception: If ClickHouse insertion fails.
    """

    if not isinstance(records, list):
        raise ValueError("records must be a list.")

    if not records:
        logger.info("No analytics records to insert.")
        return 0

    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every analytics record must be a dictionary.")

    columns = list(records[0].keys())

    if not columns:
        raise ValueError("Analytics records must contain columns.")

    for record in records:
        if list(record.keys()) != columns:
            raise ValueError(
                "All analytics records must contain the same columns "
                "in the same order."
            )

    rows = [
        [record[column] for column in columns]
        for record in records
    ]

    try:
        client.insert(
            "developer_analytics",
            rows,
            column_names=columns,
        )

        logger.info(
            "Submitted %s developer analytics records to ClickHouse.",
            len(records),
        )
        return len(records)

    except Exception:
        logger.exception("Failed to insert developer analytics.")
        raise