
"""End-to-end tests for the CogniStream analytics pipeline."""

import unittest
from datetime import datetime, timezone

import polars as pl

from src.processing.unified_analytics import run_unified_analytics


def sample_events() -> pl.DataFrame:
    base = datetime(2026, 11, 7, 9, 0, tzinfo=timezone.utc)

    rows = [
        {
            "event_id": "E001",
            "developer_id": "DEV001",
            "source": "activitywatch",
            "event_type": "coding",
            "event_timestamp": base,
            "metadata": "{}",
        },
        {
            "event_id": "E002",
            "developer_id": "DEV001",
            "source": "activitywatch",
            "event_type": "ide_activity",
            "event_timestamp": base.replace(minute=10),
            "metadata": "{}",
        },
        {
            "event_id": "E003",
            "developer_id": "DEV001",
            "source": "activitywatch",
            "event_type": "coding",
            "event_timestamp": base.replace(minute=20),
            "metadata": "{}",
        },
        {
            "event_id": "E004",
            "developer_id": "DEV001",
            "source": "slack",
            "event_type": "message",
            "event_timestamp": base.replace(minute=22),
            "metadata": "{}",
        },
    ]

    return pl.DataFrame(rows)


class TestEndToEndAnalytics(unittest.TestCase):

    def setUp(self):
        self.events_df = sample_events()

    def test_pipeline_returns_all_expected_outputs(self):
        result = run_unified_analytics(self.events_df)

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

    def test_processing_outputs_are_polars_dataframes(self):
        result = run_unified_analytics(self.events_df)

        dataframe_keys = [
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
        ]

        for key in dataframe_keys:
            with self.subTest(output=key):
                self.assertIsInstance(result[key], pl.DataFrame)

    def test_cleaned_events_have_expected_count(self):
        result = run_unified_analytics(self.events_df)

        self.assertEqual(result["cleaned_events"].height, 4)

    def test_rejected_events_have_expected_count(self):
        result = run_unified_analytics(self.events_df)

        self.assertEqual(result["rejected_events"].height, 0)

    def test_original_input_dataframe_is_not_modified(self):
        original_df = self.events_df.clone()

        run_unified_analytics(self.events_df)

        self.assertTrue(self.events_df.equals(original_df))

    def test_all_analytics_stages_are_returned(self):
        result = run_unified_analytics(self.events_df)

        stages = [
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
        ]

        for stage in stages:
            with self.subTest(stage=stage):
                self.assertIn(stage, result)
                self.assertIsInstance(result[stage], pl.DataFrame)

    def test_quality_report_contains_expected_counts(self):
        result = run_unified_analytics(self.events_df)

        report = result["quality_report"]

        self.assertIn("final_accepted_records", report)
        self.assertIn("final_rejected_records", report)
        self.assertIn("invalid_timestamp_records", report)

        self.assertEqual(report["final_accepted_records"], 4)
        self.assertEqual(report["final_rejected_records"], 0)

    def test_empty_dataframe_is_handled(self):
        empty_df = pl.DataFrame(
            schema={
                "event_id": pl.String,
                "developer_id": pl.String,
                "source": pl.String,
                "event_type": pl.String,
                "event_timestamp": pl.Datetime(
                    time_unit="us",
                    time_zone="UTC",
                ),
                "metadata": pl.String,
            }
        )

        result = run_unified_analytics(empty_df)

        self.assertEqual(result["cleaned_events"].height, 0)
        self.assertEqual(result["rejected_events"].height, 0)
        self.assertEqual(
            result["quality_report"]["final_accepted_records"], 0
        )

    def test_pipeline_rejects_non_dataframe_input(self):
        with self.assertRaises(TypeError):
            run_unified_analytics([{"event_id": "E001"}])

    def test_pipeline_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            run_unified_analytics(
                self.events_df,
                idle_threshold_minutes=0,
            )


if __name__ == "__main__":
    unittest.main()
    def test_cleaned_and_rejected_event_counts(self):
        result = run_unified_analytics(self.events_df)

        self.assertEqual(result["cleaned_events"].height, 4)
        self.assertEqual(result["rejected_events"].height, 0)