-- ==========================================
-- CogniStream Database Schema
-- Day 2: Developer Events Table
-- ==========================================

-- Create database
CREATE DATABASE IF NOT EXISTS cognistream;

-- Select database
USE cognistream;

-- Create developer events table
CREATE TABLE IF NOT EXISTS developer_events
(
    event_id String,

    developer_id String,

    source LowCardinality(String),

    event_type LowCardinality(String),

    event_timestamp DateTime64(3, 'UTC'),

    metadata String,

    event_date Date MATERIALIZED toDate(event_timestamp),

    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()

PARTITION BY toYYYYMM(event_date)

ORDER BY
(
    developer_id,
    event_timestamp,
    event_id
);

-- Verify table creation
DESCRIBE TABLE cognistream.developer_events;


### Explanation of the schema

| Column          | Data type              | Purpose                              |
| --------------- | ---------------------- | ------------------------------------ |
| event_id        | String                 | Unique activity event                |
| developer_id    | String                 | Developer identifier                 |
| source          | LowCardinality(String) | GitHub, Jira, Slack or ActivityWatch |
| event_type      | LowCardinality(String) | Activity category                    |
| event_timestamp | DateTime64(3, UTC)     | Event occurrence time                |
| metadata        | String                 | Additional JSON information          |
| event_date      | Date                   | Automatically generated event date   |
| inserted_at     | DateTime               | Database insertion time              |
