
import unittest
from datetime import datetime, timedelta, timezone

import polars as pl

from src.processing.developer_sessions import (
    detect_developer_sessions,
)


class TestDeveloperSessions(unittest.TestCase):

    def setUp(self):

        start = datetime(
            2026, 11, 4, 9, 0, tzinfo=timezone.utc
        )

        self.start = start

        self.df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "event_timestamp": start,
            },
            {
                "event_id": "E002",
                "developer_id": "DEV01",
                "event_timestamp": start + timedelta(minutes=10),
            },
            {
                "event_id": "E003",
                "developer_id": "DEV01",
                "event_timestamp": start + timedelta(minutes=20),
            },
            {
                "event_id": "E004",
                "developer_id": "DEV01",
                "event_timestamp": start + timedelta(minutes=70),
            },
            {
                "event_id": "E005",
                "developer_id": "DEV02",
                "event_timestamp": start + timedelta(minutes=5),
            },
            {
                "event_id": "E006",
                "developer_id": "DEV02",
                "event_timestamp": start + timedelta(minutes=15),
            },
        ])

    def test_session_count(self):
        sessions, _ = detect_developer_sessions(self.df)
        self.assertEqual(sessions.height, 3)

    def test_event_count(self):
        sessions, _ = detect_developer_sessions(self.df)
        self.assertEqual(sessions["event_count"].to_list(), [3, 1, 2])

    def test_session_duration(self):
        sessions, _ = detect_developer_sessions(self.df)
        self.assertEqual(
            sessions["duration_minutes"].to_list(),
            [20.0, 0.0, 10.0]
        )

    def test_session_id_assignment(self):
        _, events = detect_developer_sessions(self.df)
        self.assertEqual(events.height, 6)
        self.assertIn("session_id", events.columns)

    def test_developer_grouping(self):
        sessions, _ = detect_developer_sessions(self.df)
        self.assertEqual(
            sessions["developer_id"].to_list(),
            ["DEV01", "DEV01", "DEV02"]
        )

    def test_custom_idle_threshold(self):
        sessions, _ = detect_developer_sessions(
            self.df,
            idle_threshold_minutes=60
        )
        self.assertEqual(sessions.height, 2)

    def test_missing_columns(self):
        invalid_df = pl.DataFrame({"event_id": ["E001"]})

        with self.assertRaises(ValueError):
            detect_developer_sessions(invalid_df)

    def test_empty_dataframe(self):
        empty_df = pl.DataFrame(schema={
            "developer_id": pl.String,
            "event_timestamp": pl.Datetime("us", "UTC"),
        })

        sessions, events = detect_developer_sessions(empty_df)

        self.assertEqual(sessions.height, 0)
        self.assertEqual(events.height, 0)

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            detect_developer_sessions(
                self.df,
                idle_threshold_minutes=0
            )

    def test_exactly_30_minute_gap(self):

        df = pl.DataFrame([
            {
                "developer_id": "DEV01",
                "event_timestamp": self.start,
            },
            {
                "developer_id": "DEV01",
                "event_timestamp": self.start + timedelta(minutes=30),
            },
        ])

        sessions, _ = detect_developer_sessions(df)

        self.assertEqual(sessions.height, 1)


if __name__ == "__main__":
    unittest.main()
