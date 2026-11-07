
import polars as pl


def detect_developer_sessions(df: pl.DataFrame, idle_threshold_minutes: int = 30):

    required_columns = ["developer_id", "event_timestamp"]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if idle_threshold_minutes <= 0:
        raise ValueError("Idle threshold must be greater than zero")

    if df.is_empty():
        sessions_schema = {
            "developer_id": pl.String,
            "session_id": pl.String,
            "session_start": pl.Datetime("us", "UTC"),
            "session_end": pl.Datetime("us", "UTC"),
            "event_count": pl.UInt32,
            "duration_minutes": pl.Float64,
        }

        sessions_df = pl.DataFrame(schema=sessions_schema)

        event_sessions_df = df.with_columns(
            pl.Series("session_id", [], dtype=pl.String)
        )

        return sessions_df, event_sessions_df

    if df["developer_id"].null_count() > 0:
        raise ValueError("developer_id cannot contain null values")

    if df["event_timestamp"].null_count() > 0:
        raise ValueError("event_timestamp cannot contain null values")

    if not isinstance(df.schema["event_timestamp"], pl.Datetime):
        raise ValueError("event_timestamp must be a Datetime column")

    events = df.sort(["developer_id", "event_timestamp"])

    records = events.to_dicts()

    output_events = []
    session_records = []

    current_developer = None
    current_session_events = []
    session_number = 0

    def save_session():
        nonlocal session_number

        if not current_session_events:
            return

        start = current_session_events[0]["event_timestamp"]
        end = current_session_events[-1]["event_timestamp"]

        session_id = (
            f"{current_developer}_SESSION_{session_number}"
        )

        duration = (end - start).total_seconds() / 60

        session_records.append({
            "developer_id": current_developer,
            "session_id": session_id,
            "session_start": start,
            "session_end": end,
            "event_count": len(current_session_events),
            "duration_minutes": float(duration),
        })

        for event in current_session_events:
            event_copy = dict(event)
            event_copy["session_id"] = session_id
            output_events.append(event_copy)

    for event in records:

        developer = event["developer_id"]
        timestamp = event["event_timestamp"]

        if developer != current_developer:

            save_session()

            current_developer = developer
            current_session_events = []
            session_number = 0

        if current_session_events:

            previous_timestamp = current_session_events[-1][
                "event_timestamp"
            ]

            gap_minutes = (
                timestamp - previous_timestamp
            ).total_seconds() / 60

            if gap_minutes > idle_threshold_minutes:

                save_session()

                current_session_events = []

        if not current_session_events:
            session_number += 1

        current_session_events.append(event)

    save_session()

    sessions_schema = {
        "developer_id": pl.String,
        "session_id": pl.String,
        "session_start": pl.Datetime("us", "UTC"),
        "session_end": pl.Datetime("us", "UTC"),
        "event_count": pl.UInt32,
        "duration_minutes": pl.Float64,
    }

    sessions_df = pl.DataFrame(
        session_records,
        schema=sessions_schema
    )

    event_sessions_df = pl.DataFrame(output_events)

    return sessions_df, event_sessions_df
