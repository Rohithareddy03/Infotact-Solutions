
import unittest
import polars as pl

from src.processing.developer_metrics import (
    calculate_developer_metrics,
)


class TestDeveloperMetrics(unittest.TestCase):

    def setUp(self):

        self.events = pl.DataFrame([
            {
                "developer_id": "DEV01",
                "event_type": "commit",
            },
            {
                "developer_id": "DEV01",
                "event_type": "message",
            },
            {
                "developer_id": "DEV01",
                "event_type": "push",
            },
            {
                "developer_id": "DEV02",
                "event_type": "issue",
            },
        ])

        self.sessions = pl.DataFrame([
            {
                "developer_id": "DEV01",
                "duration_minutes": 30.0,
                "event_count": 5,
            },
            {
                "developer_id": "DEV01",
                "duration_minutes": 60.0,
                "event_count": 10,
            },
        ])

        self.transitions = pl.DataFrame([
            {
                "developer_id": "DEV01",
                "source_from": "github",
                "source_to": "slack",
            },
            {
                "developer_id": "DEV01",
                "source_from": "slack",
                "source_to": "vscode",
            },
        ])

    def test_total_events(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(dev["total_events"][0], 3)

    def test_total_commits(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(dev["total_commits"][0], 2)

    def test_total_sessions(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(dev["total_sessions"][0], 2)

    def test_estimated_activity_duration(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(
            dev["estimated_activity_minutes"][0],
            90.0,
        )

    def test_average_session_duration(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(
            dev["average_session_minutes"][0],
            45.0,
        )

    def test_context_switches(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(
            dev["total_context_switches"][0],
            2,
        )

    def test_average_events_per_session(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV01"
        )

        self.assertEqual(
            dev["average_events_per_session"][0],
            7.5,
        )

    def test_developer_without_sessions(self):
        result = calculate_developer_metrics(
            self.events,
            self.sessions,
            self.transitions,
        )

        dev = result.filter(
            pl.col("developer_id") == "DEV02"
        )

        self.assertEqual(dev["total_sessions"][0], 0)
        self.assertEqual(
            dev["estimated_activity_minutes"][0],
            0.0,
        )

    def test_missing_required_column(self):
        invalid_events = pl.DataFrame({
            "developer_id": ["DEV01"]
        })

        with self.assertRaises(ValueError):
            calculate_developer_metrics(
                invalid_events,
                self.sessions,
                self.transitions,
            )


if __name__ == "__main__":
    unittest.main()
