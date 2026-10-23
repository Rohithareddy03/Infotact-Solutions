
"""Unit tests for ClickHouse analytics preparation."""

import unittest

import polars as pl

from src.processing.clickhouse_prep import (
    ANALYTICS_COLUMNS,
    prepare_clickhouse_data,
    to_clickhouse_records,
)


class TestClickHousePrep(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame(
            {
                "developer_id": ["dev2", "dev1"],
                "total_events": [6, 10],
                "active_sources": [2, 3],
                "event_types": [3, 4],
                "context_switches": [1, 4],
                "switch_rate_pct": [20.0, 44.4],
                "activity_block_count": [1, 2],
                "total_block_events": [6, 10],
                "average_block_duration_minutes": [20.0, 22.5],
                "longest_block_duration_minutes": [20.0, 30.0],
            }
        )

    def test_output_schema(self):
        result = prepare_clickhouse_data(self.df)

        self.assertEqual(result.columns, ANALYTICS_COLUMNS)

    def test_sorted_by_developer(self):
        result = prepare_clickhouse_data(self.df)

        self.assertEqual(
            result["developer_id"].to_list(),
            ["dev1", "dev2"],
        )

    def test_count_metrics_are_integers(self):
        result = prepare_clickhouse_data(self.df)

        self.assertEqual(
            result.schema["total_events"],
            pl.Int64,
        )

    def test_optional_metrics_receive_defaults(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "total_events": [5],
            }
        )

        result = prepare_clickhouse_data(df)

        self.assertEqual(result["active_sources"][0], 0)
        self.assertIsNone(result["switch_rate_pct"][0])
        self.assertIsNone(
            result["average_block_duration_minutes"][0]
        )

    def test_duplicate_developers_rejected(self):
        df = pl.DataFrame(
            {"developer_id": ["dev1", "dev1"]}
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_data(df)

    def test_empty_developer_id_rejected(self):
        df = pl.DataFrame(
            {"developer_id": ["  "]}
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_data(df)

    def test_negative_count_rejected(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "total_events": [-1],
            }
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_data(df)

    def test_switch_rate_over_100_rejected(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "switch_rate_pct": [101.0],
            }
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_data(df)

    def test_invalid_duration_relationship_rejected(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "average_block_duration_minutes": [20.0],
                "longest_block_duration_minutes": [10.0],
            }
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_data(df)

    def test_missing_developer_id_rejected(self):
        df = pl.DataFrame({"total_events": [3]})

        with self.assertRaises(ValueError):
            prepare_clickhouse_data(df)

    def test_records_conversion(self):
        records = to_clickhouse_records(self.df)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["developer_id"], "dev1")
        self.assertEqual(
            list(records[0].keys()),
            ANALYTICS_COLUMNS,
        )

    def test_empty_dataframe(self):
        df = pl.DataFrame(
            schema={"developer_id": pl.String}
        )

        result = prepare_clickhouse_data(df)

        self.assertEqual(result.height, 0)
        self.assertEqual(result.columns, ANALYTICS_COLUMNS)


if __name__ == "__main__":
    unittest.main()
