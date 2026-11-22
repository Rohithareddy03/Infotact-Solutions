
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

    def successful_response(self, count=5):
        return SimpleNamespace(result_rows=[(count,)])

    def test_validate_string_date(self):
        result = validate_metric_date("2026-11-05")
        self.assertEqual(result, "2026-11-05")

    def test_validate_date_object(self):
        result = validate_metric_date(date(2026, 11, 5))
        self.assertEqual(result, "2026-11-05")

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            validate_metric_date("2026-13-40")

    def test_invalid_date_type(self):
        with self.assertRaises(ValueError):
            validate_metric_date(12345)

    def test_all_tables_audit_successfully(self):
        self.client.query.return_value = self.successful_response(10)

        report = audit_analytics_storage(
            self.client,
            "2026-11-05",
        )

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["total_tables"], 5)
        self.assertEqual(report["successful_tables"], 5)
        self.assertEqual(report["failed_tables"], 0)
        self.assertEqual(
            len(report["tables"]),
            len(ANALYTICS_TABLES),
        )

    def test_partial_audit_failure(self):
        self.client.query.side_effect = [
            self.successful_response(10),
            Exception("Table unavailable"),
            self.successful_response(5),
            self.successful_response(3),
            self.successful_response(2),
        ]

        report = audit_analytics_storage(
            self.client,
            "2026-11-05",
        )

        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["successful_tables"], 4)
        self.assertEqual(report["failed_tables"], 1)

    def test_all_tables_audit_failure(self):
        self.client.query.side_effect = Exception(
            "ClickHouse connection failed"
        )

        report = audit_analytics_storage(
            self.client,
            "2026-11-05",
        )

        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["successful_tables"], 0)
        self.assertEqual(report["failed_tables"], 5)

    def test_date_is_passed_as_query_parameter(self):
        self.client.query.return_value = self.successful_response(4)

        audit_analytics_storage(
            self.client,
            "2026-11-05",
        )

        first_call = self.client.query.call_args_list[0]

        self.assertEqual(
            first_call.kwargs["parameters"],
            {"metric_date": "2026-11-05"},
        )

    def test_only_predefined_tables_are_audited(self):
        self.client.query.return_value = self.successful_response(1)

        audit_analytics_storage(
            self.client,
            "2026-11-05",
        )

        self.assertEqual(
            self.client.query.call_count,
            len(ANALYTICS_TABLES),
        )


if __name__ == "__main__":
    unittest.main()
