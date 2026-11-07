"""Tests for the unified developer analytics pipeline."""

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from src.processing.unified_analytics import (
    run_unified_analytics,
    run_unified_analytics_from_file,
)


def sample_events() -> pl.DataFrame:
    base = datetime(2026, 11, 7, 9, 0, tzinfo=timezone.utc)
    rows = [
        {
            "event_id": "e1",
            "developer_id": "dev1",
            "source": "activitywatch",
            "event_type": "coding",
            "event_timestamp": base,
            "metadata": "{}",
        },
        {
            "event_id": "e2",
            "developer_id": "dev1",
            "source": "activitywatch",
            "event_type": "ide_activity",
            "event_timestamp": base.replace(minute=10),
            "metadata": "{}",
        },
        {
            "event_id": "e3",
            "developer_id": "dev1",
            "source": "activitywatch",
            "event_type": "coding",
            "event_timestamp": base.replace(minute=20),
            "metadata": "{}",
        },
        {
            "event_id": "e4",
            "developer_id": "dev1",
            "source": "slack",
            "event_type": "message",
            "event_timestamp": base.replace(minute=22),
            "metadata": "{}",
        },
    ]
    return pl.DataFrame(rows)


class TestUnifiedAnalytics(unittest.TestCase):
    def test_pipeline_returns_all_expected_outputs(self):
        result = run_unified_analytics(sample_events())

        expected_keys = {
            "cleaned_events",
            "rejected_events",
            "sessions",
            "event_sessions",
            "context_switch_summary",
            "context_switch_transitions",
            "flow_blocks",
            "event_blocks",
            "flow_summary",
            "potential_interruptions",
            "coding_events",
            "interruption_summary",
            "developer_metrics",
            "quality_report",
        }
        self.assertTrue(expected_keys.issubset(result.keys()))
        self.assertEqual(result["cleaned_events"].height, 4)
        self.assertEqual(result["quality_report"]["final_accepted_records"], 4)
        self.assertEqual(result["quality_report"]["final_rejected_records"], 0)
        self.assertIn("developer_id", result["developer_metrics"].columns)

    def test_pipeline_rejects_non_dataframe_input(self):
        with self.assertRaises(TypeError):
            run_unified_analytics([{"event_id": "e1"}])

    def test_pipeline_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            run_unified_analytics(sample_events(), idle_threshold_minutes=0)

    def test_pipeline_from_json_file(self):
        base = "2026-11-07T09:{:02d}:00Z"
        records = [
            {
                "event_id": "e1",
                "developer_id": "dev1",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": base.format(0),
                "metadata": {},
            },
            {
                "event_id": "e2",
                "developer_id": "dev1",
                "source": "activitywatch",
                "event_type": "ide_activity",
                "event_timestamp": base.format(10),
                "metadata": {},
            },
            {
                "event_id": "e3",
                "developer_id": "dev1",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": base.format(20),
                "metadata": {},
            },
            {
                "event_id": "e4",
                "developer_id": "dev1",
                "source": "slack",
                "event_type": "message",
                "event_timestamp": base.format(22),
                "metadata": {},
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "events.json"
            file_path.write_text(json.dumps(records), encoding="utf-8")
            result = run_unified_analytics_from_file(file_path)

        self.assertEqual(result["cleaned_events"].height, 4)
        self.assertEqual(result["load_rejected_events"].height, 0)
        self.assertEqual(result["quality_report"]["load_rejected_records"], 0)


if __name__ == "__main__":
    unittest.main()
