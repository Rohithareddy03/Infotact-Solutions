import unittest
from datetime import datetime, timedelta, timezone

import polars as pl

from src.processing.flow_blocks import (
    detect_flow_blocks,
    calculate_flow_summary,
)


class TestFlowBlocks(unittest.TestCase):

    def setUp(self):
        self.start = datetime(
            2026, 11, 5, 9, 0, tzinfo=timezone.utc
        )

        self.df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start,
            },
            {
                "event_id": "E002",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start + timedelta(minutes=5),
            },
            {
                "event_id": "E003",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "ide_activity",
                "event_timestamp": self.start + timedelta(minutes=10),
            },
            {
                "event_id": "E004",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "coding",
                "event_timestamp": self.start + timedelta(minutes=20),
            },
        ])

    def test_detects_activity_block(self):
        blocks, events = detect_flow_blocks(self.df)
        self.assertEqual(blocks.height, 1)
        self.assertEqual(events.height, 4)

    def test_calculates_block_duration(self):
        blocks, _ = detect_flow_blocks(self.df)
        self.assertEqual(blocks["duration_minutes"][0], 20.0)

    def test_qualifying_block(self):
        blocks, _ = detect_flow_blocks(self.df)
        self.assertTrue(blocks["is_qualifying"][0])

    def test_exact_ten_minute_gap(self):
        df = self.df.head(2).with_columns(
            pl.Series("event_timestamp", [
                self.start,
                self.start + timedelta(minutes=10),
            ])
        )
        blocks, _ = detect_flow_blocks(df)
        self.assertEqual(blocks.height, 1)

    def test_gap_greater_than_ten_minutes(self):
        df = self.df.head(2).with_columns(
            pl.Series("event_timestamp", [
                self.start,
                self.start + timedelta(minutes=11),
            ])
        )
        blocks, _ = detect_flow_blocks(df)
        self.assertEqual(blocks.height, 2)

    def test_non_coding_event_splits_block(self):
        df = pl.DataFrame([
            {**self.df.row(0, named=True)},
            {
                "event_id": "E005",
                "developer_id": "DEV01",
                "source": "activitywatch",
                "event_type": "browsing",
                "event_timestamp": self.start + timedelta(minutes=5),
            },
            {
                **self.df.row(0, named=True),
                "event_id": "E006",
                "event_timestamp": self.start + timedelta(minutes=10),
            },
        ])
        blocks, _ = detect_flow_blocks(df)
        self.assertEqual(blocks.height, 2)

    def test_multiple_developers(self):
        df = pl.concat([
            self.df,
            self.df.with_columns(
                pl.lit("DEV02").alias("developer_id")
            ),
        ])
        blocks, _ = detect_flow_blocks(df)
        self.assertEqual(blocks.height, 2)

    def test_ignores_other_sources(self):
        df = self.df.with_columns(
            pl.lit("vscode").alias("source")
        )
        blocks, events = detect_flow_blocks(df)
        self.assertEqual(blocks.height, 0)
        self.assertEqual(events.height, 0)

    def test_event_block_ids(self):
        blocks, events = detect_flow_blocks(self.df)
        self.assertIn("block_id", events.columns)
        self.assertEqual(events["block_id"].n_unique(), 1)
        self.assertEqual(events["block_id"][0], blocks["block_id"][0])

    def test_flow_summary(self):
        blocks, _ = detect_flow_blocks(self.df)
        summary = calculate_flow_summary(blocks)
        self.assertEqual(summary.height, 1)
        self.assertEqual(summary["total_blocks"][0], 1)
        self.assertEqual(summary["qualifying_blocks"][0], 1)
        self.assertEqual(summary["estimated_flow_minutes"][0], 20.0)

    def test_empty_dataframe(self):
        blocks, events = detect_flow_blocks(self.df.head(0))
        self.assertEqual(blocks.height, 0)
        self.assertEqual(events.height, 0)
        self.assertEqual(calculate_flow_summary(blocks).height, 0)


if __name__ == "__main__":
    unittest.main()
