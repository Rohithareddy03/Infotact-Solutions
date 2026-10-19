
"""Tests for the JSON event file loader."""

import json
import tempfile
import unittest
from pathlib import Path

from src.ingestion.file_loader import load_events


class TestFileLoader(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.file_path = Path(self.temp_dir.name) / "events.json"

    def test_load_valid_events(self):
        expected = [
            {"event_id": "event-1", "source": "github"},
            {"event_id": "event-2", "source": "jira"},
        ]
        self.file_path.write_text(
            json.dumps(expected), encoding="utf-8"
        )

        self.assertEqual(load_events(self.file_path), expected)

    def test_load_empty_array(self):
        self.file_path.write_text("[]", encoding="utf-8")

        self.assertEqual(load_events(self.file_path), [])

    def test_missing_file_raises_error(self):
        missing_path = Path(self.temp_dir.name) / "missing.json"

        with self.assertRaises(FileNotFoundError):
            load_events(missing_path)

    def test_invalid_json_raises_error(self):
        self.file_path.write_text("{invalid json", encoding="utf-8")

        with self.assertRaises(ValueError):
            load_events(self.file_path)

    def test_non_array_json_raises_error(self):
        self.file_path.write_text(
            '{"event_id": "event-1"}', encoding="utf-8"
        )

        with self.assertRaises(ValueError):
            load_events(self.file_path)

    def test_non_object_event_raises_error(self):
        self.file_path.write_text(
            '[{"event_id": "event-1"}, 123]', encoding="utf-8"
        )

        with self.assertRaises(ValueError):
            load_events(self.file_path)


if __name__ == "__main__":
    unittest.main()
