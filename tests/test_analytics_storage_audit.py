

import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from src.database.analytics_storage_audit import (
    ANALYTICS_TABLES,
    audit_analytics_storage,
    validate_metric_date,
)


class TestAnalyticsStorageAudit(unittest.TestCase):

    def setUp(self):
        self.client = Mock()

    def make_response(self, count):
        return SimpleNamespace(result_rows=[(count,)])

    def test_valid_metric_date(self):
        self.assertEqual(
            validate_metric_date(date(2026, 11, 22)),
            "2026-11-22",
        )

    def test_invalid_metric_date(self):
        with self.assertRaises(ValueError):
            validate_metric_date("2026-15-40")

    def test_missing_clickhouse_client(self):
        report = audit_analytics_storage(
            None,
            "2026-11-22",
        )

        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["successful_tables"], 0)
        self.assertEqual(report["failed_tables"], 5)
        self.assertEqual(report["total_records"], 0)
        self.assertEqual(len(report["errors"]), 5)

    def test_successful_audit_of_all_tables(self):
        self.client.query.return_value = self.make_response(10)

        report = audit_analytics_storage(
            self.client,
            "2026-11-22",
        )

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["total_tables"], 5)
        self.assertEqual(report["successful_tables"], 5)
        self.assertEqual(report["failed_tables"], 0)
        self.assertEqual(self.client.query.call_count, 5)

    def test_partial_audit_failure(self):
        self.client.query.side_effect = [
            self.make_response(10),
            Exception("Table unavailable"),
            self.make_response(5),
            self.make_response(3),
            self.make_response(2),
        ]

        report = audit_analytics_storage(
            self.client,
            "2026-11-22",
        )

        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["successful_tables"], 4)
        self.assertEqual(report["failed_tables"], 1)
        self.assertIn("context_switches", report["errors"])

    def test_complete_audit_failure(self):
        self.client.query.side_effect = Exception(
            "ClickHouse connection failed"
        )

        report = audit_analytics_storage(
            self.client,
            "2026-11-22",
        )

        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["successful_tables"], 0)
        self.assertEqual(report["failed_tables"], 5)
        self.assertEqual(report["total_records"], 0)

    def test_audit_selected_tables_only(self):
        self.client.query.return_value = self.make_response(7)

        selected = [
            "developer_sessions",
            "flow_blocks",
        ]

        report = audit_analytics_storage(
            self.client,
            "2026-11-22",
            selected_tables=selected,
        )

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["total_tables"], 2)
        self.assertEqual(report["successful_tables"], 2)
        self.assertEqual(
            list(report["tables"].keys()),
            selected,
        )
        self.assertEqual(self.client.query.call_count, 2)

    def test_unknown_table_names(self):
        with self.assertRaises(ValueError):
            audit_analytics_storage(
                self.client,
                "2026-11-22",
                selected_tables=["unknown_table"],
            )

        self.client.query.assert_not_called()

    def test_correct_total_record_calculation(self):
        counts = [10, 20, 30, 40, 50]
        self.client.query.side_effect = [
            self.make_response(count) for count in counts
        ]

        report = audit_analytics_storage(
            self.client,
            "2026-11-22",
        )

        self.assertEqual(report["total_records"], 150)
        self.assertEqual(
            report["total_records"],
            sum(
                item["record_count"]
                for item in report["tables"].values()
            ),
        )


if __name__ == "__main__":
    unittest.main()
