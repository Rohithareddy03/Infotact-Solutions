import polars as pl
from datetime import datetime

REQUIRED_COLUMNS = [
    "event_id",
    "developer_id",
    "source",
    "event_type",
    "event_timestamp",
    "metadata",
]

ALLOWED_SOURCES = {
    "github",
    "jira",
    "slack",
    "activitywatch",
}


def _valid_timestamp(value):
    if value is None:
        return False

    if isinstance(value, datetime):
        return True

    if isinstance(value, str):
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            return False

    return False


def clean_developer_events(df: pl.DataFrame):

    if not isinstance(df, pl.DataFrame):
        raise TypeError("Input must be a Polars DataFrame")

    missing_columns = [
        col for col in REQUIRED_COLUMNS if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df.is_empty():
        rejected_schema = dict(df.schema)
        rejected_schema["rejection_reason"] = pl.String

        rejected_df = pl.DataFrame(schema=rejected_schema)

        report = {
            "total_records": 0,
            "accepted_records": 0,
            "rejected_records": 0,
            "duplicate_records": 0,
        }

        return df.clone(), rejected_df, report

    accepted = []
    rejected = []
    seen_event_ids = set()
    duplicate_count = 0

    for row in df.iter_rows(named=True):

        reason = None

        for column in REQUIRED_COLUMNS:
            value = row[column]

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                reason = f"missing_{column}"
                break

        if reason is None:
            if not _valid_timestamp(row["event_timestamp"]):
                reason = "invalid_event_timestamp"

        if reason is None:
            if row["source"].strip().lower() not in ALLOWED_SOURCES:
                reason = "unsupported_source"

        if reason is None:
            event_id = row["event_id"]

            if event_id in seen_event_ids:
                reason = "duplicate_event_id"
                duplicate_count += 1
            else:
                seen_event_ids.add(event_id)

        if reason:
            rejected_row = row.copy()
            rejected_row["rejection_reason"] = reason
            rejected.append(rejected_row)
        else:
            accepted.append(row)

    cleaned_df = (
        pl.DataFrame(accepted, schema=df.schema)
        if accepted else pl.DataFrame(schema=df.schema)
    )

    rejected_schema = dict(df.schema)
    rejected_schema["rejection_reason"] = pl.String

    rejected_df = (
        pl.DataFrame(rejected, schema=rejected_schema)
        if rejected else pl.DataFrame(schema=rejected_schema)
    )

    report = {
        "total_records": df.height,
        "accepted_records": cleaned_df.height,
        "rejected_records": rejected_df.height,
        "duplicate_records": duplicate_count,
    }

    return cleaned_df, rejected_df, report
