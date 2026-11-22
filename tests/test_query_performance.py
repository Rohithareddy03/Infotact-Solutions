
import unittest
from unittest.mock import Mock, patch

from src.database.query_performance import (
    execute_monitored_query,
    benchmark_analytics_queries,
    run_database_health_check,
)


class TestQueryPerformance(unittest.TestCase):

    def setUp(self):
        self.client = Mock()

        self.query_result = Mock()
        self.query_result.result_rows = [
            ("DEV01", 10),
            ("DEV02", 15),
        ]

        self.client.query.return_value = self.query_result

    def test_successful_query(self):
        report = execute_monitored_query(
            self.client, "SELECT 1"
        )

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["rows_returned"], 2)

    def test_execution_time_recorded(self):
        report = execute_monitored_query(
            self.client, "SELECT 1"
        )

        self.assertGreaterEqual(
            report["execution_time_ms"], 0
        )

    def test_slow_query_identification(self):
        with patch(
            "src.database.query_performance.time.perf_counter",
            side_effect=[1.0, 2.0],
        ):
            report = execute_monitored_query(
                self.client,
                "SELECT 1",
                slow_threshold_ms=500,
            )

        self.assertTrue(report["slow_query"])

    def test_failed_query(self):
        self.client.query.side_effect = Exception(
            "Database connection failed"
        )

        report = execute_monitored_query(
            self.client, "SELECT 1"
        )

        self.assertEqual(report["status"], "failed")
        self.assertIn("Database connection failed", report["error"])

    def test_empty_query_validation(self):
        with self.assertRaises(ValueError):
            execute_monitored_query(
                self.client, ""
            )

    def test_negative_threshold_validation(self):
        with self.assertRaises(ValueError):
            execute_monitored_query(
                self.client,
                "SELECT 1",
                slow_threshold_ms=-1,
            )

    def test_query_parameters(self):
        execute_monitored_query(
            self.client,
            "SELECT * FROM developers WHERE id = {id:String}",
            parameters={"id": "DEV01"},
        )

        self.client.query.assert_called_once_with(
            "SELECT * FROM developers WHERE id = {id:String}",
            parameters={"id": "DEV01"},
        )

    def test_benchmark_summary(self):
        queries = {
            "developer_kpis": "SELECT 1",
            "sessions": "SELECT 2",
        }

        report = benchmark_analytics_queries(
            queries,
            client=self.client,
        )

        self.assertEqual(report["total_queries"], 2)
        self.assertEqual(report["successful_queries"], 2)
        self.assertEqual(report["failed_queries"], 0)

    def test_benchmark_failed_query(self):
        self.client.query.side_effect = [
            self.query_result,
            Exception("Query failed"),
        ]

        report = benchmark_analytics_queries(
            {
                "kpis": "SELECT 1",
                "sessions": "SELECT 2",
            },
            client=self.client,
        )

        self.assertEqual(report["successful_queries"], 1)
        self.assertEqual(report["failed_queries"], 1)

    def test_database_health_check(self):
        report = run_database_health_check(
            client=self.client
        )

        self.assertEqual(report["status"], "success")
        self.client.query.assert_called_once_with("SELECT 1")


if __name__ == "__main__":
    unittest.main()
