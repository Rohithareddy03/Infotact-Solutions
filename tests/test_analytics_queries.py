import unittest
from unittest.mock import Mock, patch

import polars as pl

from src.database.analytics_queries import (
    validate_date_range,
    execute_analytics_query,
    get_developer_kpis,
    get_session_analysis,
    get_interruption_analysis,
    get_total_developer_commits,
    get_activity_duration,
    get_average_session_duration,
    get_uninterrupted_activity_blocks,
    get_context_switch_frequency,
    get_interruption_count,
    get_daily_activity_summary,
)


class TestAnalyticsQueries(unittest.TestCase):

    def setUp(self):
        self.client = Mock()
        self.result = Mock()

        self.result.column_names = [
            "developer_id",
            "total_commits",
        ]

        self.result.result_rows = [
            ("DEV01", 10),
        ]

        self.client.query.return_value = self.result

    def test_successful_commit_count(self):
        response = get_total_developer_commits(
            "2026-11-01",
            "2026-11-05",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(
            response["data"][0]["total_commits"],
            10,
        )

    def test_activity_duration(self):
        self.result.column_names = [
            "developer_id",
            "estimated_activity_minutes",
        ]
        self.result.result_rows = [
            ("DEV01", 120.5),
        ]

        response = get_activity_duration(
            "2026-11-01",
            "2026-11-05",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(
            response["data"][0]["estimated_activity_minutes"],
            120.5,
        )

    def test_average_session_duration(self):
        self.result.column_names = [
            "developer_id",
            "session_count",
            "average_session_minutes",
        ]
        self.result.result_rows = [
            ("DEV01", 5, 30.5),
        ]

        response = get_average_session_duration(
            "2026-11-01",
            "2026-11-05",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(
            response["data"][0]["average_session_minutes"],
            30.5,
        )

    def test_empty_results(self):
        self.result.result_rows = []

        response = get_total_developer_commits(
            "2026-11-01",
            "2026-11-05",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [])
        self.assertIsNone(response["error"])

    def test_database_connection_failure(self):
        with patch(
            "src.database.analytics_queries.create_clickhouse_client",
            side_effect=Exception("Connection failed"),
        ):
            response = get_total_developer_commits(
                "2026-11-01",
                "2026-11-05",
            )

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["data"], [])
        self.assertIn("Connection failed", response["error"])

    def test_invalid_date_range(self):
        with self.assertRaises(ValueError):
            get_total_developer_commits(
                "2026-11-10",
                "2026-11-01",
                client=self.client,
            )

    def test_developer_id_filtering(self):
        response = get_total_developer_commits(
            "2026-11-01",
            "2026-11-05",
            developer_id="DEV01",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")

        parameters = self.client.query.call_args.kwargs[
            "parameters"
        ]

        self.assertEqual(
            parameters["developer_id"],
            "DEV01",
        )

        query = self.client.query.call_args.args[0]

        self.assertIn(
            "developer_id = {developer_id:String}",
            query,
        )

    def test_daily_activity_summary(self):
        self.result.column_names = [
            "metric_date",
            "developer_id",
            "total_events",
            "total_commits",
        ]
        self.result.result_rows = [
            ("2026-11-01", "DEV01", 100, 10),
        ]

        response = get_daily_activity_summary(
            "2026-11-01",
            "2026-11-05",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(
            response["data"][0]["developer_id"],
            "DEV01",
        )
        self.assertEqual(
            response["data"][0]["total_events"],
            100,
        )

    def test_correct_query_result_handling(self):
        self.result.column_names = [
            "developer_id",
            "context_switch_count",
        ]
        self.result.result_rows = [
            ("DEV01", 8),
            ("DEV02", 12),
        ]

        response = get_context_switch_frequency(
            "2026-11-01",
            "2026-11-05",
            client=self.client,
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["data"]), 2)
        self.assertEqual(
            response["data"][1]["context_switch_count"],
            12,
        )

    def test_existing_polars_functions_remain_compatible(self):
        result = execute_analytics_query(
            self.client,
            "SELECT 1",
            {},
        )

        self.assertIsInstance(result, pl.DataFrame)

    def test_existing_analysis_functions_remain_available(self):
        with patch(
            "src.database.analytics_queries._load_sql",
            return_value="SELECT 1",
        ):
            self.assertIsInstance(
                get_developer_kpis(
                    "2026-11-01",
                    "2026-11-05",
                    client=self.client,
                ),
                pl.DataFrame,
            )

            self.assertIsInstance(
                get_session_analysis(
                    "2026-11-01",
                    "2026-11-05",
                    client=self.client,
                ),
                pl.DataFrame,
            )

            self.assertIsInstance(
                get_interruption_analysis(
                    "2026-11-01",
                    "2026-11-05",
                    client=self.client,
                ),
                pl.DataFrame,
            )


if __name__ == "__main__":
    unittest.main()