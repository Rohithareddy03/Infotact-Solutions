
"""Unit tests for the developer event ingestion pipeline."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    @patch("src.ingestion.pipeline.time.sleep")
    @patch("src.ingestion.pipeline.load_events")
    def test_pipeline_recovers_after_temporary_failure(
        self, mock_load, mock_sleep
    ):
        events = [self.valid_event()]
        mock_load.side_effect = [
            OSError("Temporary read error"),
            events,
        ]

        valid, invalid = process_event_file(
            self.file_path,
            max_attempts=3,
            retry_delay=1,
        )

        self.assertEqual(valid, events)
        self.assertEqual(invalid, [])
        self.assertEqual(mock_load.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("src.ingestion.pipeline.time.sleep")
    @patch("src.ingestion.pipeline.load_events")
    def test_pipeline_fails_after_all_retry_attempts(
        self, mock_load, mock_sleep
    ):
        mock_load.side_effect = OSError("File access failed")

        with self.assertRaises(OSError):
            process_event_file(
                self.file_path,
                max_attempts=3,
                retry_delay=1,
            )

        self.assertEqual(mock_load.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("src.ingestion.pipeline.load_events")
    def test_missing_file_is_not_retried(self, mock_load):
        mock_load.side_effect = FileNotFoundError("Missing file")

        with self.assertRaises(FileNotFoundError):
            process_event_file(
                self.file_path,
                max_attempts=3,
                retry_delay=0,
            )

        self.assertEqual(mock_load.call_count, 1)

    def test_invalid_max_attempts_is_rejected(self):
        with self.assertRaises(ValueError):
            process_event_file(
                self.file_path,
                max_attempts=0,
                retry_delay=0,
            )

    def test_negative_retry_delay_is_rejected(self):
        with self.assertRaises(ValueError):
            process_event_file(
                self.file_path,
                max_attempts=3,
                retry_delay=-1,
            )


if __name__ == "__main__":
    unittest.main()
