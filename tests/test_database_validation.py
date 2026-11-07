
import unittest
from unittest.mock import Mock

from src.database.database_validation import (
    REQUIRED_TABLES,
    check_database_connection,
    check_duplicate_events,
    check_negative_durations,
    check_query_performance,
    validate_database,
)


class TestDatabaseValidation(unittest.TestCase):

    def setUp(self):
        self.client = Mock()

    def test_database_connection_success(self):
        result = Mock()
        result.result_rows = [(1,)]
        self.client.query.return_value = result

        self.assertTrue(
            check_database_connection(self.client)
        )

    def test_database_connection_failure(self):
        self.client.query.side_effect = Exception(
            "Connection failed"
        )

        self.assertFalse(
            check_database_connection(self.client)
        )

    def test_query_performance_success(self):
        result = Mock()
        result.result_rows = [(1,)]
        self.client.query.return_value = result

        response = check_query_performance(self.client)

        self.assertTrue(response["success"])
        self.assertIsNotNone(response["execution_time_ms"])

    def test_validate_database_success(self):
        existing_tables = list(REQUIRED_TABLES)

        def query_side_effect(sql, **kwargs):
            result = Mock()

            if sql.startswith("SHOW TABLES"):
                result.result_rows = [
                    (table,) for table in existing_tables
                ]

            elif sql.startswith("DESCRIBE TABLE"):
                table_name = sql.split(".")[-1]
                result.result_rows = [
                    (column,) for column in
                    REQUIRED_TABLES[table_name]
                ]

            elif sql.startswith("SELECT count()"):
                result.result_rows = [(10,)]

            return result

        self.client.query.side_effect = query_side_effect

        report = validate_database(self.client)

        self.assertTrue(report["overall_valid"])
        self.assertEqual(report["missing_tables"], [])
        self.assertEqual(report["total_records"], 60)

    def test_validate_database_missing_table(self):
        existing_tables = [
            table for table in REQUIRED_TABLES
            if table != "flow_blocks"
        ]

        def query_side_effect(sql, **kwargs):
            result = Mock()

            if sql.startswith("SHOW TABLES"):
                result.result_rows = [
                    (table,) for table in existing_tables
                ]

            elif sql.startswith("DESCRIBE TABLE"):
                table_name = sql.split(".")[-1]
                result.result_rows = [
                    (column,) for column in
                    REQUIRED_TABLES[table_name]
                ]

            elif sql.startswith("SELECT count()"):
                result.result_rows = [(10,)]

            return result

        self.client.query.side_effect = query_side_effect

        report = validate_database(self.client)

        self.assertFalse(report["overall_valid"])
        self.assertIn(
            "flow_blocks",
            report["missing_tables"],
        )

    def test_validate_database_missing_columns(self):
        def query_side_effect(sql, **kwargs):
            result = Mock()

            if sql.startswith("SHOW TABLES"):
                result.result_rows = [
                    (table,) for table in REQUIRED_TABLES
                ]

            elif sql.startswith("DESCRIBE TABLE"):
                table_name = sql.split(".")[-1]
                columns = REQUIRED_TABLES[table_name]

                if table_name == "developer_events":
                    columns = columns[:-1]

                result.result_rows = [
                    (column,) for column in columns
                ]

            elif sql.startswith("SELECT count()"):
                result.result_rows = [(10,)]

            return result

        self.client.query.side_effect = query_side_effect

        report = validate_database(self.client)

        self.assertFalse(report["overall_valid"])
        self.assertIn(
            "developer_events",
            report["missing_columns"],
        )

    def test_check_duplicate_events(self):
        result = Mock()
        result.result_rows = [
            ("event_101", 2),
            ("event_205", 3),
        ]
        self.client.query.return_value = result

        response = check_duplicate_events(self.client)

        self.assertTrue(response["has_duplicates"])
        self.assertEqual(response["duplicate_count"], 2)

    def test_check_negative_durations(self):
        sessions_result = Mock()
        sessions_result.result_rows = [(2,)]

        blocks_result = Mock()
        blocks_result.result_rows = [(1,)]

        self.client.query.side_effect = [
            sessions_result,
            blocks_result,
        ]

        response = check_negative_durations(self.client)

        self.assertEqual(
            response["negative_session_durations"], 2
        )
        self.assertEqual(
            response["negative_flow_block_durations"], 1
        )
        self.assertEqual(
            response["total_negative_durations"], 3
        )


if __name__ == "__main__":
    unittest.main()
