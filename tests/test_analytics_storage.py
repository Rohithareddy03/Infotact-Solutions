import unittest
from unittest.mock import Mock

import polars as pl

from src.database.analytics_storage import (
    insert_analytics_dataframe,
)


class TestAnalyticsStorage(unittest.TestCase):

    def setUp(self):
        self.client = Mock()

        self.sessions = pl.DataFrame({
            "developer_id": ["DEV01"],
            "session_start": [
                "2026-11-05 09:00:00"
            ],
            "session_end": [
                "2026-11-05 09:30:00"
            ],
            "event_count": [5],
            "duration_minutes": [30.0],
        })

    def test_insert_sessions(self):
        count = insert_analytics_dataframe(
            self.client,
            "developer_sessions",
            self.sessions,
        )

        self.assertEqual(count, 1)
        self.client.insert.assert_called_once()

    def test_correct_table_name(self):
        insert_analytics_dataframe(
            self.client,
            "developer_sessions",
            self.sessions,
        )

        args, kwargs = self.client.insert.call_args

        self.assertEqual(
            args[0],
            "developer_sessions"
        )

    def test_correct_column_names(self):
        insert_analytics_dataframe(
            self.client,
            "developer_sessions",
            self.sessions,
        )

        _, kwargs = self.client.insert.call_args

        self.assertEqual(
            kwargs["column_names"],
            [
                "developer_id",
                "session_start",
                "session_end",
                "event_count",
                "duration_minutes",
            ],
        )

    def test_empty_dataframe(self):
        empty_df = self.sessions.clear()

        count = insert_analytics_dataframe(
            self.client,
            "developer_sessions",
            empty_df,
        )

        self.assertEqual(count, 0)
        self.client.insert.assert_not_called()

    def test_missing_columns(self):
        invalid_df = pl.DataFrame({
            "developer_id": ["DEV01"]
        })

        with self.assertRaises(ValueError):
            insert_analytics_dataframe(
                self.client,
                "developer_sessions",
                invalid_df,
            )

        self.client.insert.assert_not_called()

    def test_invalid_table_name(self):
        with self.assertRaises(ValueError):
            insert_analytics_dataframe(
                self.client,
                "invalid_table",
                self.sessions,
            )


if __name__ == "__main__":
    unittest.main()