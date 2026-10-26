"""Tests for ClickHouse analytics export preparation."""

import unittest
from datetime import date

import polars as pl

from src.processing.clickhouse_export import (
    prepare_clickhouse_records,
)


class TestClickHouseExport(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev2"],
                "total_events": [10, 5],
                "active_sources": [3, 2],
                "event_types": [4, 3],
                "context_switches": [4, 1],
                "switch_rate_pct": [44.4, 25.0],
                "activity_block_count": [2, 1],
                "total_block_events": [10, 5],
                "average_block_duration_minutes": [22.5, 12.0],
                "longest_block_duration_minutes": [30.0, 12.0],
            }
        )

    def test_converts_dataframe_to_records(self):
        records = prepare_clickhouse_records(
            self.df, "2026-10-26"
        )

        self.assertEqual(len(records), 2)
        self.assertIsInstance(records, list)
        self.assertIsInstance(records[0], dict)

    def test_snapshot_date_is_added(self):
        records = prepare_clickhouse_records(
            self.df, "2026-10-26"
        )

        self.assertEqual(
            records[0]["snapshot_date"],
            date(2026, 10, 26),
        )

    def test_metric_values_are_preserved(self):
        records = prepare_clickhouse_records(
            self.df, "2026-10-26"
        )

        dev1 = next(
            row for row in records
            if row["developer_id"] == "dev1"
        )

        self.assertEqual(dev1["total_events"], 10)
        self.assertEqual(dev1["context_switches"], 4)
        self.assertEqual(
            dev1["average_block_duration_minutes"],
            22.5,
        )

    def test_missing_count_metrics_default_to_zero(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1"],
                "total_events": [5],
            }
        )

        records = prepare_clickhouse_records(
            df, "2026-10-26"
        )

        self.assertEqual(records[0]["total_events"], 5)
        self.assertEqual(records[0]["context_switches"], 0)
        self.assertEqual(records[0]["activity_block_count"], 0)

    def test_empty_dataframe_returns_empty_list(self):
        df = pl.DataFrame(
            schema={"developer_id": pl.String}
        )

        records = prepare_clickhouse_records(
            df, "2026-10-26"
        )

        self.assertEqual(records, [])

    def test_duplicate_developers_are_rejected(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev1"],
                "total_events": [5, 7],
            }
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_records(
                df, "2026-10-26"
            )

    def test_invalid_snapshot_date_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare_clickhouse_records(
                self.df, "26-10-2026"
            )

    def test_missing_developer_id_is_rejected(self):
        df = pl.DataFrame(
            {"total_events": [5]}
        )

        with self.assertRaises(ValueError):
            prepare_clickhouse_records(
                df, "2026-10-26"
            )


if __name__ == "__main__":
    unittest.main()