# Developer Activity Data Processing

## Objective
Clean and transform developer activity events
before storing them in ClickHouse.

## Technology
- Python
- Polars
- JSON

## Planned Processing Steps

### 1. Data Cleaning
- Remove invalid records.
- Handle missing values.
- Validate required fields.

### 2. Timestamp Normalization
- Convert timestamps into UTC.
- Ensure consistent datetime formats.
- Handle invalid timestamps.

### 3. Event Processing
- Group events by developer.
- Sort events chronologically.
- Remove duplicate events.

### 4. Activity Analysis
- Calculate total developer events.
- Calculate activity duration.
- Identify activity sessions.
- Detect context switches.
- Identify interruptions.

## Expected Output
Cleaned and structured developer activity
data ready for ClickHouse storage.