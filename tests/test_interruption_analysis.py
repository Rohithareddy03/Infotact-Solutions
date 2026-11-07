import unittest
from datetime import datetime, timedelta, timezone

import polars as pl

from src.processing.interruption_analysis import (
    detect_potential_interruptions,
    calculate_interruption_summary,
)


class TestInterruptionAnalysis(unittest.TestCase):

    def setUp(self):
        start = datetime(
            2026, 11, 5, 9, 0,
            tzinfo=timezone.utc
        )

        self.start = start

        self.df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": start,
            },
            {
                "event_id": "E002",
                "developer_id": "DEV01",
                "source": "slack",
                "event_type": "message",
                "event_timestamp": start + timedelta(minutes=2),
            },
            {
                "event_id": "E003",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "ide_activity",
                "event_timestamp": start + timedelta(minutes=10),
            },
            {
                "event_id": "E004",
                "developer_id": "DEV01",
                "source": "slack",
                "event_type": "notification",
                "event_timestamp": start + timedelta(minutes=12),
            },
        ])

    def test_detects_potential_interruptions(self):
        interruptions, coding = detect_potential_interruptions(
            self.df
        )
        self.assertEqual(interruptions.height, 2)
        self.assertEqual(coding.height, 2)

    def test_matches_correct_event_ids(self):
        interruptions, _ = detect_potential_interruptions(
            self.df
        )
        self.assertEqual(
            set(interruptions["coding_event_id"].to_list()),
            {"E001", "E003"},
        )
        self.assertEqual(
            set(interruptions["interruption_event_id"].to_list()),
            {"E002", "E004"},
        )

    def test_calculates_delay(self):
        interruptions, _ = detect_potential_interruptions(
            self.df
        )
        self.assertEqual(
            sorted(interruptions["delay_minutes"].to_list()),
            [2.0, 2.0],
        )

    def test_exact_five_minute_window(self):
        df = self.df.head(2).with_columns(
            pl.Series("event_timestamp", [
                self.start,
                self.start + timedelta(minutes=5),
            ])
        )
        interruptions, _ = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 1)

    def test_event_outside_window_is_not_matched(self):
        df = self.df.head(2).with_columns(
            pl.Series("event_timestamp", [
                self.start,
                self.start + timedelta(minutes=6),
            ])
        )
        interruptions, _ = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 0)

    def test_slack_before_coding_is_not_matched(self):
        df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "source": "slack",
                "event_type": "message",
                "event_timestamp": self.start,
            },
            {
                "event_id": "E002",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start + timedelta(minutes=2),
            },
        ])
        interruptions, _ = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 0)

    def test_one_coding_event_matches_only_once(self):
        df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start,
            },
            {
                "event_id": "E002",
                "developer_id": "DEV01",
                "source": "slack",
                "event_type": "message",
                "event_timestamp": self.start + timedelta(minutes=1),
            },
            {
                "event_id": "E003",
                "developer_id": "DEV01",
                "source": "slack",
                "event_type": "notification",
                "event_timestamp": self.start + timedelta(minutes=2),
            },
        ])
        interruptions, _ = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 1)

    def test_slack_event_matches_only_once(self):
        df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start,
            },
            {
                "event_id": "E002",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start + timedelta(minutes=1),
            },
            {
                "event_id": "E003",
                "developer_id": "DEV01",
                "source": "slack",
                "event_type": "message",
                "event_timestamp": self.start + timedelta(minutes=2),
            },
        ])
        interruptions, _ = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 1)

    def test_separates_developers(self):
        df = pl.concat([
            self.df,
            self.df.with_columns(
                pl.lit("DEV02").alias("developer_id")
            ),
        ])
        interruptions, coding = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 4)
        self.assertEqual(coding.height, 4)
        self.assertEqual(
            set(interruptions["developer_id"].to_list()),
            {"DEV01", "DEV02"},
        )

    def test_ignores_unrelated_events(self):
        df = pl.concat([
            self.df,
            pl.DataFrame([{
                "event_id": "E005",
                "developer_id": "DEV01",
                "source": "browser",
                "event_type": "message",
                "event_timestamp": self.start + timedelta(minutes=3),
            }]),
        ])
        interruptions, _ = detect_potential_interruptions(df)
        self.assertEqual(interruptions.height, 2)

    def test_coding_match_status(self):
        _, coding = detect_potential_interruptions(self.df)
        self.assertTrue(coding["is_matched"].all())
        self.assertIn(
            "matched_interruption_event_id",
            coding.columns,
        )

    def test_calculates_interruption_summary(self):
        interruptions, coding = detect_potential_interruptions(
            self.df
        )
        summary = calculate_interruption_summary(
            interruptions, coding
        )
        self.assertEqual(summary.height, 1)
        self.assertEqual(summary["total_coding_events"][0], 2)
        self.assertEqual(summary["potential_interruptions"][0], 2)
        self.assertEqual(
            summary["interruption_rate_percent"][0], 100.0
        )

    def test_handles_empty_dataframe(self):
        empty = self.df.head(0)

        interruptions, coding = detect_potential_interruptions(
            empty
        )

        self.assertEqual(interruptions.height, 0)
        self.assertEqual(coding.height, 0)

        summary = calculate_interruption_summary(
            interruptions, coding
        )
        self.assertEqual(summary.height, 0)


if __name__ == "__main__":
    unittest.main()
