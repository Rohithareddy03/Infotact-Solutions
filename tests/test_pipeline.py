"""Unit tests for the developer event ingestion pipeline."""

import json
import tempfile
import unittest
from pathlib import Path

from src.ingestion.pipeline import process_event_file


class TestIngestionPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = Path(self.temp_dir.name) / "events.json"

    def write_events(self, events):
        self.file_path.write_text(
            json.dumps(events),
            encoding="utf-8",
        )

    def valid_event(self):
        return {
            "event_id": "event-001",
            "developer_id": "developer-001",
            "source": "github",
            "event_type": "commit",
            "event_timestamp": "2026-10-19T10:00:00+00:00",
            "metadata": {"repository": "cognistream"},
        }

    def test_all_events_valid(self):
        events = [self.valid_event()]
        self.write_events(events)

        valid, invalid = process_event_file(self.file_path)

        self.assertEqual(valid, events)
        self.assertEqual(invalid, [])

    def test_invalid_event_is_rejected(self):
        event = self.valid_event()
        event.pop("developer_id")
        self.write_events([event])

        valid, invalid = process_event_file(self.file_path)

        self.assertEqual(valid, [])
        self.assertEqual(len(invalid), 1)
        self.assertIn("reason", invalid[0])
        self.assertEqual(invalid[0]["event"], event)

    def test_mixed_valid_and_invalid_events(self):
        valid_event = self.valid_event()
        invalid_event = self.valid_event()
        invalid_event["event_id"] = "event-002"
        invalid_event["source"] = "unknown_source"

        self.write_events([valid_event, invalid_event])

        valid, invalid = process_event_file(self.file_path)

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)
        self.assertEqual(valid[0]["event_id"], "event-001")
        self.assertEqual(
            invalid[0]["event"]["event_id"],
            "event-002",
        )

    def test_empty_file_array(self):
        self.write_events([])

        valid, invalid = process_event_file(self.file_path)

        self.assertEqual(valid, [])
        self.assertEqual(invalid, [])

    def test_missing_file_raises_error(self):
        missing_file = Path(self.temp_dir.name) / "missing.json"

        with self.assertRaises(FileNotFoundError):
            process_event_file(missing_file)


if __name__ == "__main__":
    unittest.main()