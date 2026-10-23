"""Tests for unified CogniStream analytics."""

import unittest

import polars as pl

from src.processing.unified_analytics import build_unified_analytics


class TestUnifiedAnalytics(unittest.TestCase):

    def setUp(self):
        self.activity_metrics = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev2"],
                "total_events": [10, 6],
                "active_sources": [3, 2],
                "event_types": [4, 3],
            }
        )

        self.context_metrics = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev2"],
                "context_switches": [4, 1],
                "switch_rate_pct": [44.4, 20.0],
            }
        )

        self.activity_blocks = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev1", "dev2"],
                "block_number": [1, 2, 1],
                "event_count": [6, 4, 6],
                "duration_minutes": [30.0, 15.0, 20.0],
            }
        )

    def test_one_row_per_developer(self):
        result = build_unified_analytics(
            self.activity_metrics,
            self.context_metrics,
            self.activity_blocks,
        )

        self.assertEqual(result.height, 2)
        self.assertEqual(
            result["developer_id"].n_unique(),
            2,
        )

    def test_activity_metrics_are_retained(self):
        result = build_unified_analytics(
            self.activity_metrics,
            self.context_metrics,
            self.activity_blocks,
        )

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["total_events"][0], 10)

    def test_context_metrics_are_retained(self):
        result = build_unified_analytics(
            self.activity_metrics,
            self.context_metrics,
            self.activity_blocks,
        )

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["context_switches"][0], 4)

    def test_activity_blocks_are_aggregated(self):
        result = build_unified_analytics(
            self.activity_metrics,
            self.context_metrics,
            self.activity_blocks,
        )

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["activity_block_count"][0], 2)
        self.assertEqual(dev1["total_block_events"][0], 10)
        self.assertEqual(
            dev1["average_block_duration_minutes"][0],
            22.5,
        )
        self.assertEqual(
            dev1["longest_block_duration_minutes"][0],
            30.0,
        )

    def test_missing_developer_id_is_rejected(self):
        invalid_df = pl.DataFrame(
            {"total_events": [5]}
        )

        with self.assertRaises(ValueError):
            build_unified_analytics(
                invalid_df,
                self.context_metrics,
                self.activity_blocks,
            )

    def test_duplicate_developers_are_rejected(self):
        duplicate_metrics = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev1"],
                "total_events": [5, 6],
            }
        )

        with self.assertRaises(ValueError):
            build_unified_analytics(
                duplicate_metrics,
                self.context_metrics,
                self.activity_blocks,
            )

    def test_empty_activity_blocks(self):
        empty_blocks = pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "event_count": pl.UInt32,
                "duration_minutes": pl.Float64,
            }
        )

        result = build_unified_analytics(
            self.activity_metrics,
            self.context_metrics,
            empty_blocks,
        )

        self.assertEqual(result.height, 2)
        self.assertEqual(
            result["activity_block_count"].to_list(),
            [0, 0],
        )


if __name__ == "__main__":
    unittest.main()