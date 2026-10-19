
"""Data-quality checks for transformed developer activity events."""

import polars as pl


REQUIRED_COLUMNS = [
    "event_id",
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
    "metadata",
]


def generate_quality_report(df: pl.DataFrame) -> dict:
    """Report missing values, empty strings, and duplicate event IDs."""

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    null_counts = {}
    empty_string_counts = {}

    for column in REQUIRED_COLUMNS:
        values = df.get_column(column).to_list()

        null_counts[column] = sum(
            value is None for value in values
        )

        empty_string_counts[column] = sum(
            isinstance(value, str) and not value.strip()
            for value in values
        )

    event_ids = df.get_column("event_id").to_list()
    seen_ids = set()
    duplicate_ids = set()

    for event_id in event_ids:
        if event_id is None:
            continue

        if event_id in seen_ids:
            duplicate_ids.add(event_id)
        else:
            seen_ids.add(event_id)

    duplicate_row_count = sum(
        event_id in duplicate_ids
        for event_id in event_ids
        if event_id is not None
    ) - len(duplicate_ids)

    # Any null or blank required value makes the data fail quality checks.
    has_missing_values = any(null_counts.values())
    has_empty_values = any(empty_string_counts.values())
    has_duplicates = bool(duplicate_ids)

    return {
        "total_rows": df.height,
        "duplicate_event_ids": sorted(duplicate_ids),
        "duplicate_extra_rows": duplicate_row_count,
        "null_counts": null_counts,
        "empty_string_counts": empty_string_counts,
        "is_valid": not (
            has_missing_values
            or has_empty_values
            or has_duplicates
        ),
    }
