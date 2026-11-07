import json
import tempfile
import unittest
from pathlib import Path

import polars as pl

from src.processing.load_developer_events import (
    load_json_events,
    validate_event_records,
    events_to_dataframe,
    process_event_file,
)


def create_event():
    return {
        "event_id": "EVT001",
        "developer_id": "DEV001",
        "source": "github",
        "event_type": "commit",
        "event_timestamp": "2026-11-04T09:00:00+00:00",
        "metadata": {"repository": "cognistream"},
    }


class TestDeveloperEventLoading(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "events.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_json(self, data):
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file)

    def test_01_load_json_events(self):
        self.write_json([create_event()])
        events = load_json_events(self.file_path)
        self.assertEqual(len(events), 1)

    def test_02_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_json_events("missing.json")

    def test_03_json_must_be_list(self):
        self.write_json({"event": create_event()})
        with self.assertRaises(ValueError):
            load_json_events(self.file_path)

    def test_04_validate_valid_event(self):
        valid, rejected = validate_event_records([create_event()])
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(rejected), 0)

    def test_05_missing_required_column(self):
        event = create_event()
        del event["developer_id"]
        valid, rejected = validate_event_records([event])
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)

    def test_06_invalid_timestamp(self):
        event = create_event()
        event["event_timestamp"] = "invalid-date"
        valid, rejected = validate_event_records([event])
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)

    def test_07_invalid_metadata(self):
        event = create_event()
        event["metadata"] = "invalid"
        valid, rejected = validate_event_records([event])
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(rejected), 1)

    def test_08_dataframe_schema(self):
        valid, _ = validate_event_records([create_event()])
        df = events_to_dataframe(valid)
        self.assertIsInstance(df, pl.DataFrame)
        self.assertEqual(df.height, 1)
        self.assertEqual(df.width, 6)
        self.assertEqual(
            df.schema["event_timestamp"],
            pl.Datetime("us", "UTC")
        )

    def test_09_metadata_serialization(self):
        valid, _ = validate_event_records([create_event()])
        df = events_to_dataframe(valid)
        metadata = json.loads(df["metadata"][0])
        self.assertEqual(metadata["repository"], "cognistream")

    def test_10_empty_dataframe(self):
        df = events_to_dataframe([])
        self.assertEqual(df.height, 0)
        self.assertEqual(df.width, 6)

    def test_11_process_event_file(self):
        self.write_json([create_event()])
        clean_df, rejected_df = process_event_file(self.file_path)
        self.assertEqual(clean_df.height, 1)
        self.assertEqual(rejected_df.height, 0)


if __name__ == "__main__":
    unittest.main()