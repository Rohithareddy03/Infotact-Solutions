CREATE DATABASE IF NOT EXISTS cognistream;

CREATE TABLE IF NOT EXISTS cognistream.developer_analytics
(
    snapshot_date Date,
    developer_id String,

    total_events UInt64 DEFAULT 0,
    active_sources UInt32 DEFAULT 0,
    event_types UInt32 DEFAULT 0,

    context_switches UInt32 DEFAULT 0,
    switch_rate_pct Nullable(Float64),
    average_gap_minutes Nullable(Float64),

    activity_block_count UInt32 DEFAULT 0,
    total_block_events UInt64 DEFAULT 0,
    average_block_duration_minutes Nullable(Float64),
    longest_block_duration_minutes Nullable(Float64),

    first_activity Nullable(String),
    last_activity Nullable(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(snapshot_date)
ORDER BY (snapshot_date, developer_id);