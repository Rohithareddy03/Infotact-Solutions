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
- ### Implemented

Created the initial ClickHouse developer_events table.

### Database
cognistream

### Table
developer_events

### Storage Engine
MergeTree

### Partitioning
Monthly partitioning using event_date.

### Sorting
developer_id, event_timestamp, event_id.

### Features
- UTC timestamp storage.
- Automatic event_date generation.
- LowCardinality columns for source and event_type.
- Additional event metadata stored as JSON text.
- Insertion timestamp tracking.

### Validation
The schema can be verified using:

DESCRIBE TABLE cognistream.developer_events;

Sample records can be checked using:

SELECT * FROM cognistream.developer_events;


## 6. How to create the files using PowerShell

If your original project folder is:


C:\Users\rohit\OneDrive\Desktop\cognistream


Run:


cd "C:\Users\rohit\OneDrive\Desktop\cognistream"

New-Item -ItemType Directory -Force .\sql\schema


Create and edit the three files using VS Code:


code .\sql\schema\developer_events.sql
code .\sql\sample_insert.sql
code .\sql\README.md


Paste the corresponding content into each file and save.

## 7. Validate the SQL in ClickHouse

If ClickHouse is installed and running, execute the schema SQL using your ClickHouse client.

For example, with clickhouse-client:


clickhouse-client --multiquery --queries-file="sql/schema/developer_events.sql"


Then execute:


clickhouse-client --multiquery --queries-file="sql/sample_insert.sql"


Verify the table:


SELECT count()
FROM cognistream.developer_events;


Expected sample count: 4.

If ClickHouse is not installed or running yet, commit the SQL files and validate them when the database environment is available. Do not report database execution as successful without actually running it.

## 8. Copy files into Member 2's GitHub branch

Switch to the cloned repository:


cd "C:\Users\rohit\OneDrive\Desktop\Infotact-Solutions"


Create the destination folder:


New-Item -ItemType Directory -Force .\sql\schema


Copy the files:


Copy-Item "C:\Users\rohit\OneDrive\Desktop\cognistream\sql\schema\developer_events.sql" .\sql\schema\ -Force

Copy-Item "C:\Users\rohit\OneDrive\Desktop\cognistream\sql\sample_insert.sql" .\sql\ -Force

Copy-Item "C:\Users\rohit\OneDrive\Desktop\cognistream\sql\README.md" .\sql\ -Force


