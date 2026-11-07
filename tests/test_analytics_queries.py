import unittest
from unittest.mock import Mock

import polars as pl

from src.database.analytics_queries import (
    validate_date_range,
    execute_analytics_query,
    get_developer_kpis,
    get_session_analysis,
    get_interruption_analysis,
)


class TestAnalyticsQueries(unittest.TestCase):

    def setUp(self):
        self.client = Mock()

        self.query_result = Mock()

        self.query_result.result_rows = [
            ("DEV01", 10)
        ]

        self.query_result.column_names = [
            "developer_id",
            "total_events",
        ]

        self.client.query.return_value = (
            self.query_result
        )

    def test_valid_date_range(self):

        result = validate_date_range(
            "2026-11-01",
            "2026-11-05",
        )

        self.assertEqual(
            result,
            ("2026-11-01", "2026-11-05"),
        )

    def test_invalid_date_format(self):

        with self.assertRaises(ValueError):

            validate_date_range(
                "01-11-2026",
                "05-11-2026",
            )

    def test_start_date_after_end_date(self):

        with self.assertRaises(ValueError):

            validate_date_range(
                "2026-11-10",
                "2026-11-01",
            )

    def test_execute_query(self):

        result = execute_analytics_query(
            self.client,
            "SELECT 1",
            {},
        )

        self.assertIsInstance(
            result,
            pl.DataFrame,
        )

        self.assertEqual(
            result.shape,
            (1, 2),
        )

    def test_execute_query_passes_parameters(self):

        execute_analytics_query(
            self.client,
            "SELECT 1",
            {"developer_id": "DEV01"},
        )

        self.client.query.assert_called_once_with(
            "SELECT 1",
            parameters={"developer_id": "DEV01"},
        )

    def test_get_developer_kpis(self):

        result = get_developer_kpis(
            "2026-11-01",
            "2026-11-30",
            client=self.client,
        )

        self.assertIsInstance(result, pl.DataFrame)

        parameters = self.client.query.call_args.kwargs[
            "parameters"
        ]

        self.assertEqual(
            parameters["start_date"],
            "2026-11-01",
        )

        self.assertEqual(
            parameters["end_date"],
            "2026-11-30",
        )

    def test_get_session_analysis(self):

        result = get_session_analysis(
            "2026-11-01",
            "2026-11-30",
            client=self.client,
        )

        self.assertIsInstance(result, pl.DataFrame)

        parameters = self.client.query.call_args.kwargs[
            "parameters"
        ]

        self.assertEqual(
            parameters["end_date_exclusive"],
            "2026-12-01",
        )

    def test_get_interruption_analysis(self):

        result = get_interruption_analysis(
            "2026-11-01",
            "2026-11-30",
            client=self.client,
        )

        self.assertIsInstance(result, pl.DataFrame)

        self.assertTrue(
            self.client.query.called
        )


if __name__ == "__main__":
    unittest.main()