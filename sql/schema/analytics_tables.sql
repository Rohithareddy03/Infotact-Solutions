CREATE DATABASE IF NOT EXISTS cognistream;

USE cognistream;


-- 1. Developer activity sessions
CREATE TABLE IF NOT EXISTS developer_sessions
(
    developer_id String,
    session_start DateTime64(3, 'UTC'),
    session_end DateTime64(3, 'UTC'),
    event_count UInt32,
    duration_minutes Float64,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (developer_id, session_start);


-- 2. Context-switch transitions
CREATE TABLE IF NOT EXISTS context_switches
(
    developer_id String,
    from_source LowCardinality(String),
    to_source LowCardinality(String),
    from_timestamp DateTime64(3, 'UTC'),
    to_timestamp DateTime64(3, 'UTC'),
    gap_minutes Float64,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (developer_id, from_timestamp);


-- 3. Uninterrupted activity blocks
CREATE TABLE IF NOT EXISTS flow_blocks
(
    developer_id String,
    block_start DateTime64(3, 'UTC'),
    block_end DateTime64(3, 'UTC'),
    duration_minutes Float64,
    event_count UInt32,
    qualifies UInt8,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (developer_id, block_start);


-- 4. Potential interruptions
CREATE TABLE IF NOT EXISTS potential_interruptions
(
    developer_id String,
    slack_event_id String,
    coding_event_id String,
    interruption_timestamp DateTime64(3, 'UTC'),
    minutes_after_coding Float64,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (developer_id, interruption_timestamp);


-- 5. Daily developer metrics
CREATE TABLE IF NOT EXISTS developer_daily_metrics
(
    metric_date Date,
    developer_id String,
    total_events UInt32,
    total_commits UInt32,
    total_sessions UInt32,
    estimated_activity_minutes Float64,
    average_session_minutes Float64,
    average_events_per_session Float64,
    total_context_switches UInt32,
    total_blocks UInt32,
    qualifying_blocks UInt32,
    estimated_flow_minutes Float64,
    total_coding_events UInt32,
    potential_interruptions UInt32,
    interruption_rate_pct Float64,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(metric_date)
ORDER BY (metric_date, developer_id);