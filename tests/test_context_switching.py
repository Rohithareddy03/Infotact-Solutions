"""Tests for developer context-switching analytics."""

import unittest

import polars as pl

from src.processing.context_switching import (
    analyze_context_switches,
)


class TestContextSwitching(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame(
            {
                "developer_id": [
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev2",
                    "dev2",
                ],
                "source": [
                    "github",
                    "github",
                    "slack",
                    "jira",
                    "github",
                    "slack",
                    "slack",
                ],
                "event_timestamp": [
                    "2026-10-20T09:00:00+00:00",
                    "2026-10-20T09:05:00+00:00",
                    "2026-10-20T09:08:00+00:00",
                    "2026-10-20T09:15:00+00:00",
                    "2026-10-20T09:20:00+00:00",
                    "2026-10-20T10:00:00+00:00",
                    "2026-10-20T10:10:00+00:00",
                ],
            }
        )

    def test_one_row_per_developer(self):
        result = analyze_context_switches(self.df)
        self.assertEqual(result.height, 2)

    def test_context_switch_count(self):
        result = analyze_context_switches(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1["context_switches"][0], 3)

    def test_switch_rate(self):
        result = analyze_context_switches(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertAlmostEqual(
            dev1["switch_rate_pct"][0],
            75.0,
        )

    def test_same_source_has_no_switches(self):
        result = analyze_context_switches(self.df)

        dev2 = result.filter(
            pl.col("developer_id") == "dev2"
        )

        self.assertEqual(dev2["context_switches"][0], 0)

    def test_average_gap(self):
        result = analyze_context_switches(self.df)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        # Gaps: 5, 3, 7 and 5 minutes.
        self.assertAlmostEqual(
            dev1["average_gap_minutes"][0],
            5.0,
        )

    def test_empty_dataframe(self):
        empty_df = pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "source": pl.String,
                "event_timestamp": pl.String,
            }
        )

        result = analyze_context_switches(empty_df)

        self.assertEqual(result.height, 0)
        self.assertIn("context_switches", result.columns)

    def test_missing_required_column(self):
        invalid_df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "source": ["github"],
            }
        )

        with self.assertRaises(ValueError):
            analyze_context_switches(invalid_df)


if __name__ == "__main__":
    unittest.main()