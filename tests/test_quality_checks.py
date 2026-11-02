"""Tests for CogniStream ingestion quality checks."""

import unittest

from src.ingestion.quality_checks import (
    validate_event_schema,
    validate_event_timestamp,
    validate_event_batch,
)


def make_event(event_id="event_001"):
    return {
        "event_id": event_id,
        "developer_id": "dev_001",
        "source": "github",
        "event_type": "commit",
        "event_timestamp": "2026-11-02T09:00:00+00:00",
        "metadata": {"repository": "cognistream"},
    }


class TestEventSchema(unittest.TestCase):

    def test_valid_event(self):
        valid, errors = validate_event_schema(make_event())

        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_required_field(self):
        event = make_event()
        del event["developer_id"]

        valid, errors = validate_event_schema(event)

        self.assertFalse(valid)
        self.assertTrue(any("developer_id" in e for e in errors))

    def test_unsupported_source(self):
        event = make_event()
        event["source"] = "unknown"

        valid, errors = validate_event_schema(event)

        self.assertFalse(valid)
        self.assertTrue(any("source" in e for e in errors))

    def test_metadata_must_be_dictionary(self):
        event = make_event()
        event["metadata"] = "invalid"

        valid, errors = validate_event_schema(event)

        self.assertFalse(valid)
        self.assertTrue(any("metadata" in e for e in errors))

    def test_non_dictionary_event(self):
        valid, errors = validate_event_schema("invalid")

        self.assertFalse(valid)
        self.assertTrue(errors)


class TestEventTimestamp(unittest.TestCase):

    def test_timezone_aware_timestamp(self):
        valid, message = validate_event_timestamp(make_event())

        self.assertTrue(valid)

    def test_timestamp_without_timezone(self):
        event = make_event()
        event["event_timestamp"] = "2026-11-02T09:00:00"

        valid, message = validate_event_timestamp(event)

        self.assertFalse(valid)

    def test_invalid_timestamp(self):
        event = make_event()
        event["event_timestamp"] = "not-a-date"

        valid, message = validate_event_timestamp(event)

        self.assertFalse(valid)


class TestEventBatch(unittest.TestCase):

    def test_batch_counts(self):
        events = [
            make_event("event_001"),
            make_event("event_002"),
        ]

        report = validate_event_batch(events)

        self.assertEqual(report["total_events"], 2)
        self.assertEqual(report["accepted_events"], 2)
        self.assertEqual(report["rejected_events"], 0)

    def test_duplicate_event_ids(self):
        events = [
            make_event("event_001"),
            make_event("event_001"),
            make_event("event_002"),
        ]

        report = validate_event_batch(events)

        self.assertEqual(report["accepted_events"], 2)
        self.assertEqual(report["duplicate_extra_rows"], 1)
        self.assertEqual(
            report["duplicate_event_ids"],
            ["event_001"],
        )

    def test_invalid_events_are_rejected(self):
        event = make_event()
        event["event_timestamp"] = "invalid"

        report = validate_event_batch([event])

        self.assertEqual(report["accepted_events"], 0)
        self.assertEqual(report["rejected_events"], 1)

    def test_non_list_batch_is_rejected(self):
        with self.assertRaises(TypeError):
            validate_event_batch("invalid")


if __name__ == "__main__":
    unittest.main()