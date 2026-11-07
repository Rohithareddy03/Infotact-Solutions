import unittest
from datetime import datetime, timedelta, timezone

import polars as pl

from src.processing.context_switch_analysis import (
    analyze_context_switches,
)


class TestContextSwitchAnalysis(unittest.TestCase):

    def setUp(self):
        start = datetime(
            2026, 11, 4, 9, 0, tzinfo=timezone.utc
        )

        self.df = pl.DataFrame([
            {
                "developer_id": "DEV01",
                "source": "github",
                "event_timestamp": start,
            },
            {
                "developer_id": "DEV01",
                "source": "github",
                "event_timestamp": start + timedelta(minutes=5),
            },
            {
                "developer_id": "DEV01",
                "source": "slack",
                "event_timestamp": start + timedelta(minutes=10),
            },
            {
                "developer_id": "DEV01",
                "source": "jira",
                "event_timestamp": start + timedelta(minutes=15),
            },
            {
                "developer_id": "DEV01",
                "source": "jira",
                "event_timestamp": start + timedelta(minutes=20),
            },
            {
                "developer_id": "DEV02",
                "source": "github",
                "event_timestamp": start,
            },
            {
                "developer_id": "DEV02",
                "source": "slack",
                "event_timestamp": start + timedelta(minutes=10),
            },
        ])

    def test_returns_two_dataframes(self):
        summary, transitions = analyze_context_switches(self.df)
        self.assertIsInstance(summary, pl.DataFrame)
        self.assertIsInstance(transitions, pl.DataFrame)

    def test_developer_count(self):
        summary, _ = analyze_context_switches(self.df)
        self.assertEqual(summary.height, 2)

    def test_total_events(self):
        summary, _ = analyze_context_switches(self.df)
        dev01 = summary.filter(pl.col("developer_id") == "DEV01")
        self.assertEqual(dev01["total_events"][0], 5)

    def test_detects_source_changes(self):
        _, transitions = analyze_context_switches(self.df)
        self.assertEqual(transitions.height, 3)

    def test_switch_count_per_developer(self):
        summary, _ = analyze_context_switches(self.df)
        dev01 = summary.filter(pl.col("developer_id") == "DEV01")
        self.assertEqual(dev01["total_switches"][0], 2)

    def test_switch_rate(self):
        summary, _ = analyze_context_switches(self.df)
        dev01 = summary.filter(pl.col("developer_id") == "DEV01")
        self.assertAlmostEqual(dev01["switch_rate"][0], 0.5)

    def test_ignores_idle_gap_over_threshold(self):
        start = datetime(
            2026, 11, 4, 9, 0, tzinfo=timezone.utc
        )

        df = pl.DataFrame([
            {
                "developer_id": "DEV01",
                "source": "github",
                "event_timestamp": start,
            },
            {
                "developer_id": "DEV01",
                "source": "slack",
                "event_timestamp": start + timedelta(minutes=45),
            },
        ])

        summary, transitions = analyze_context_switches(df)
        self.assertEqual(transitions.height, 0)
        self.assertEqual(summary["total_switches"][0], 0)

    def test_custom_idle_threshold(self):
        _, transitions = analyze_context_switches(
            self.df, idle_threshold_minutes=5
        )
        self.assertEqual(transitions.height, 2)

    def test_sorts_events_by_timestamp(self):
        _, transitions = analyze_context_switches(self.df.reverse())
        self.assertEqual(transitions.height, 3)

    def test_empty_dataframe(self):
        empty_df = pl.DataFrame(schema={
            "developer_id": pl.String,
            "source": pl.String,
            "event_timestamp": pl.Datetime(time_zone="UTC"),
        })

        summary, transitions = analyze_context_switches(empty_df)
        self.assertEqual(summary.height, 0)
        self.assertEqual(transitions.height, 0)

    def test_invalid_inputs(self):
        with self.assertRaises(TypeError):
            analyze_context_switches([])

        with self.assertRaises(ValueError):
            analyze_context_switches(
                self.df, idle_threshold_minutes=0
            )

    def test_missing_columns(self):
        invalid_df = pl.DataFrame({
            "developer_id": ["DEV01"],
            "source": ["github"],
        })

        with self.assertRaises(ValueError):
            analyze_context_switches(invalid_df)


if __name__ == "__main__":
    unittest.main()
