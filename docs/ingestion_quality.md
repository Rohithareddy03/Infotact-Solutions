# CogniStream Ingestion Quality Checks

## Purpose

Validate developer activity events before they enter the
analytics processing pipeline.

## Validation rules

1. Required event fields must be present.
2. Event IDs and developer IDs must not be empty.
3. Event sources must be GitHub, Jira, Slack, or ActivityWatch.
4. Event type must be a non-empty string.
5. Metadata must be a dictionary.
6. Timestamps must be valid ISO timestamps with a timezone.
7. Duplicate event IDs are detected within each batch.

## Duplicate handling

The first valid occurrence of an event ID is retained.
Additional occurrences are excluded from the accepted batch.

## Quality report

The validation module returns:

- total_events
- accepted_events
- rejected_events
- duplicate_event_ids
- duplicate_extra_rows
- valid_events
- invalid_events

## Airflow integration

The ingestion task validates events before passing them
to the analytics task.

Accepted events and the quality summary are passed
separately through Airflow XCom.

## Limitations

- Duplicate detection is within a single batch.
- Invalid events are reported but not persisted to a
  separate quarantine database.
- XCom is intended for small payloads, not large datasets.
- Validation does not establish whether an event is
  factually correct at its original source.