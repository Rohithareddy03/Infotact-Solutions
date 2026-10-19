
"""Tests for developer event transformations."""

import unittest
from datetime import date, datetime, timezone

import polars as pl

from src.processing.transform_events import transform_events


class TestTransformEvents(unittest.TestCase):

    def setUp(self):
        self.event = {
            "event_id": "event-001",
            "developer_id": "developer-001",
            "source": "GitHub",
            "event_type": "Commit",
            "event_timestamp": "2026-10-19T10:30:00+05:30",
            "metadata": {"repository": "cognistream"},
        }

    def test_transforms_event_to_dataframe(self):
        df = transform_events([self.event])

        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.height, 1)
        self.assertIn("event_date", df.columns)
        self.assertIn("event_hour", df.columns)

    def test_normalizes_source_and_event_type(self):
        df = transform_events([self.event])

        self.assertEqual(df["source"][0], "github")
        self.assertEqual(df["event_type"][0], "commit")

    def test_converts_timestamp_to_utc(self):
        df = transform_events([self.event])

        timestamp = df["event_timestamp"][0]
        self.assertEqual(
            timestamp,
            datetime(2026, 10, 19, 5, 0, tzinfo=timezone.utc),
        )

    def test_extracts_date_and_hour(self):
        df = transform_events([self.event])

        self.assertEqual(df["event_date"][0], date(2026, 10, 19))
        self.assertEqual(df["event_hour"][0], 5)

    def test_serializes_metadata(self):
        import json

        df = transform_events([self.event])
        metadata = json.loads(df["metadata"][0])

        self.assertEqual(metadata["repository"], "cognistream")

    def test_empty_events_return_empty_dataframe(self):
        df = transform_events([])

        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.height, 0)
        self.assertIn("event_id", df.columns)

    def test_missing_required_field_raises_error(self):
        event = self.event.copy()
        del event["developer_id"]

        with self.assertRaises(ValueError):
            transform_events([event])

    def test_timezone_naive_timestamp_is_rejected(self):
        event = self.event.copy()
        event["event_timestamp"] = "2026-10-19T10:30:00"

        with self.assertRaises(ValueError):
            transform_events([event])


if __name__ == "__main__":
    unittest.main()
