"""Unit tests for developer activity metrics."""

import unittest

import polars as pl

from src.processing.developer_metrics import (
    calculate_developer_metrics,
)


class TestDeveloperMetrics(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame(
            {
                "developer_id": [
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev2",
                ],
                "source": [
                    "github",
                    "jira",
                    "github",
                    "slack",
                ],
                "event_type": [
                    "commit",
                    "issue_updated",
                    "pull_request",
                    "message",
                ],
                "event_timestamp": [
                    "2026-10-20T09:00:00+00:00",
                    "2026-10-20T09:15:00+00:00",
                    "2026-10-20T09:30:00+00:00",
                    "2026-10-20T10:00:00+00:00",
                ],
            }
        )

    def test_one_row_per_developer(self):
        result = calculate_developer_metrics(self.df)

        self.assertEqual(result.height, 2)

    def test_total_events(self):
        result = calculate_developer_metrics(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["total_events"][0], 3)

    def test_active_sources(self):
        result = calculate_developer_metrics(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["active_sources"][0], 2)

    def test_event_types(self):
        result = calculate_developer_metrics(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["event_types"][0], 3)

    def test_activity_span(self):
        result = calculate_developer_metrics(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertAlmostEqual(
            dev1["activity_span_minutes"][0],
            30.0,
        )

    def test_empty_dataframe(self):
        empty_df = pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "source": pl.String,
                "event_type": pl.String,
                "event_timestamp": pl.String,
            }
        )

        result = calculate_developer_metrics(empty_df)

        self.assertEqual(result.height, 0)
        self.assertIn("total_events", result.columns)

    def test_missing_required_column(self):
        invalid_df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "source": ["github"],
            }
        )

        with self.assertRaises(ValueError):
            calculate_developer_metrics(invalid_df)


if __name__ == "__main__":
    unittest.main()