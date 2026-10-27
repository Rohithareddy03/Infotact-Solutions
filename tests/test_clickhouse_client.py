"""Tests for ClickHouse client and analytics insertion utilities."""

import unittest
from unittest.mock import MagicMock, patch

from src.database.clickhouse_client import (
    create_clickhouse_client,
    insert_developer_analytics,
)


class TestCreateClickHouseClient(unittest.TestCase):

    @patch("src.database.clickhouse_client.clickhouse_connect.get_client")
    def test_create_client_uses_environment_configuration(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "CLICKHOUSE_HOST": "localhost",
                "CLICKHOUSE_PORT": "8123",
                "CLICKHOUSE_USER": "default",
                "CLICKHOUSE_PASSWORD": "test-password",
                "CLICKHOUSE_DATABASE": "cognistream",
            },
        ):
            client = create_clickhouse_client()

        self.assertIs(client, mock_client)
        mock_get_client.assert_called_once_with(
            host="localhost",
            port=8123,
            username="default",
            password="test-password",
            database="cognistream",
        )

    @patch("src.database.clickhouse_client.clickhouse_connect.get_client")
    def test_connection_error_is_raised(self, mock_get_client):
        mock_get_client.side_effect = RuntimeError("Connection failed")

        with self.assertRaises(RuntimeError):
            create_clickhouse_client()


class TestInsertDeveloperAnalytics(unittest.TestCase):

    def setUp(self):
        self.client = MagicMock()
        self.records = [
            {
                "snapshot_date": "2026-10-27",
                "developer_id": "dev_001",
                "total_events": 20,
            },
            {
                "snapshot_date": "2026-10-27",
                "developer_id": "dev_002",
                "total_events": 15,
            },
        ]

    def test_inserts_records_and_returns_count(self):
        result = insert_developer_analytics(
            self.client, self.records
        )

        self.assertEqual(result, 2)
        self.client.insert.assert_called_once_with(
            "developer_analytics",
            [
                ["2026-10-27", "dev_001", 20],
                ["2026-10-27", "dev_002", 15],
            ],
            column_names=[
                "snapshot_date",
                "developer_id",
                "total_events",
            ],
        )

    def test_empty_records_do_not_call_database(self):
        result = insert_developer_analytics(self.client, [])

        self.assertEqual(result, 0)
        self.client.insert.assert_not_called()

    def test_non_list_input_is_rejected(self):
        with self.assertRaises(ValueError):
            insert_developer_analytics(self.client, "invalid")

    def test_non_dictionary_record_is_rejected(self):
        with self.assertRaises(ValueError):
            insert_developer_analytics(
                self.client, [{"developer_id": "dev_001"}, "invalid"]
            )

    def test_records_with_different_columns_are_rejected(self):
        records = [
            {"developer_id": "dev_001", "total_events": 10},
            {"developer_id": "dev_002", "context_switches": 4},
        ]

        with self.assertRaises(ValueError):
            insert_developer_analytics(self.client, records)

        self.client.insert.assert_not_called()

    def test_insertion_error_is_raised(self):
        self.client.insert.side_effect = RuntimeError(
            "Database unavailable"
        )

        with self.assertRaises(RuntimeError):
            insert_developer_analytics(self.client, self.records)


if __name__ == "__main__":
    unittest.main()