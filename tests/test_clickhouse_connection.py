
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.database.clickhouse_connection import (
    ClickHouseConnectionError,
    create_clickhouse_client,
    check_connection,
    insert_developer_events,
)


class TestClickHouseConnection(unittest.TestCase):

    @patch(
        "src.database.clickhouse_connection.clickhouse_connect.get_client"
    )
    def test_create_client(self, mock_get_client):
        mock_get_client.return_value = Mock()

        client = create_clickhouse_client()

        self.assertIsNotNone(client)
        mock_get_client.assert_called_once()

    @patch(
        "src.database.clickhouse_connection.clickhouse_connect.get_client"
    )
    def test_client_creation_failure(self, mock_get_client):
        mock_get_client.side_effect = Exception("Connection failed")

        with self.assertRaises(ClickHouseConnectionError):
            create_clickhouse_client()

    def test_check_connection_success(self):
        client = Mock()
        client.ping.return_value = True

        self.assertTrue(check_connection(client))

    def test_check_connection_failure(self):
        client = Mock()
        client.ping.side_effect = Exception("Server unavailable")

        self.assertFalse(check_connection(client))

    def test_insert_valid_events(self):
        client = Mock()

        events = [{
            "developer_id": "DEV001",
            "event_type": "code_commit",
            "event_timestamp": datetime.now(timezone.utc),
            "metadata": {"language": "Python"},
        }]

        result = insert_developer_events(client, events)

        self.assertEqual(result, 1)
        client.insert.assert_called_once()

        inserted_rows = client.insert.call_args[0][1]
        self.assertEqual(inserted_rows[0][0], "DEV001")
        self.assertEqual(inserted_rows[0][1], "code_commit")
        self.assertEqual(inserted_rows[0][3], '{"language": "Python"}')

    def test_insert_empty_events(self):
        client = Mock()

        with self.assertRaises(ValueError):
            insert_developer_events(client, [])

        client.insert.assert_not_called()

    def test_insert_missing_required_field(self):
        client = Mock()

        events = [{
            "developer_id": "DEV001",
            "event_type": "code_commit",
            "metadata": {},
        }]

        with self.assertRaises(ValueError):
            insert_developer_events(client, events)

        client.insert.assert_not_called()

    def test_insert_naive_timestamp(self):
        client = Mock()

        events = [{
            "developer_id": "DEV001",
            "event_type": "code_commit",
            "event_timestamp": datetime.now(),
            "metadata": {},
        }]

        with self.assertRaises(ValueError):
            insert_developer_events(client, events)

        client.insert.assert_not_called()

    def test_database_insertion_failure(self):
        client = Mock()
        client.insert.side_effect = Exception("Database error")

        events = [{
            "developer_id": "DEV001",
            "event_type": "code_commit",
            "event_timestamp": datetime.now(timezone.utc),
            "metadata": {},
        }]

        with self.assertRaises(ClickHouseConnectionError):
            insert_developer_events(client, events)


if __name__ == "__main__":
    unittest.main()
