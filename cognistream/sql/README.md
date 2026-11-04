ClickHouse Database Design

## Project
CogniStream - Developer Flow-State &
Cognitive Load Analytics

## Objective
ClickHouse is used as the analytical database
for storing and analyzing developer activity events.

## Database Name
cognistream

## Planned Tables

### 1. developer_events
Stores raw developer activity events.

### 2. developer_analytics
Stores aggregated developer activity metrics.

## Developer Events Table Fields

| Column | Data Type | Description |
|---|---|---|
| event_id | String | Unique event identifier |
| developer_id | String | Developer identifier |
| source | String | GitHub, Jira, Slack or ActivityWatch |
| event_type | String | Type of activity |
| event_timestamp | DateTime64 | Event timestamp |
| metadata | String | Additional event information |

## Storage Engine
MergeTree

## Partitioning
Partition by event date.

## Sorting
Order by developer_id and event_timestamp.

## Future Work
- Create ClickHouse database.
- Implement table schemas.
- Load processed events.
- Develop analytical SQL queries.
