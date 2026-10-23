"""Unit tests for developer activity block detection."""

import unittest

import polars as pl

from src.processing.activity_blocks import detect_activity_blocks


class TestActivityBlocks(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame(
            {
                "developer_id": [
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev1",
                    "dev2",
                    "dev2",
                ],
                "event_timestamp": [
                    "2026-10-20T09:00:00+00:00",
                    "2026-10-20T09:05:00+00:00",
                    "2026-10-20T09:12:00+00:00",
                    "2026-10-20T09:40:00+00:00",
                    "2026-10-20T09:45:00+00:00",
                    "2026-10-20T10:00:00+00:00",
                    "2026-10-20T10:10:00+00:00",
                ],
            }
        )

    def test_detects_activity_blocks(self):
        result = detect_activity_blocks(self.df, 15)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(dev1.height, 2)

    def test_block_event_counts(self):
        result = detect_activity_blocks(self.df, 15)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(
            dev1["event_count"].to_list(),
            [3, 2],
        )

    def test_block_durations(self):
        result = detect_activity_blocks(self.df, 15)

        dev1 = result.filter(
            pl.col("developer_id") == "dev1"
        )

        self.assertEqual(
            dev1["duration_minutes"].to_list(),
            [12.0, 5.0],
        )

    def test_gap_equal_to_threshold_stays_in_block(self):
        df = pl.DataFrame(
            {
                "developer_id": ["dev1", "dev1"],
                "event_timestamp": [
                    "2026-10-20T09:00:00+00:00",
                    "2026-10-20T09:15:00+00:00",
                ],
            }
        )

        result = detect_activity_blocks(df, 15)

        self.assertEqual(result.height, 1)
        self.assertEqual(result["event_count"][0], 2)

    def test_multiple_developers_are_separated(self):
        result = detect_activity_blocks(self.df, 15)

        self.assertEqual(
            result.get_column("developer_id").n_unique(),
            2,
        )

    def test_empty_dataframe(self):
        empty_df = pl.DataFrame(
            schema={
                "developer_id": pl.String,
                "event_timestamp": pl.String,
            }
        )

        result = detect_activity_blocks(empty_df)

        self.assertEqual(result.height, 0)
        self.assertIn("duration_minutes", result.columns)

    def test_missing_required_column(self):
        df = pl.DataFrame(
            {"developer_id": ["dev1"]}
        )

        with self.assertRaises(ValueError):
            detect_activity_blocks(df)

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            detect_activity_blocks(self.df, -1)

    def test_invalid_input_type(self):
        with self.assertRaises(TypeError):
            detect_activity_blocks([{"developer_id": "dev1"}])


if __name__ == "__main__":
    unittest.main()