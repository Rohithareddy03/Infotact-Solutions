import unittest
from datetime import datetime, timezone

import polars as pl

from src.processing.clean_developer_events import clean_developer_events


class TestCleanDeveloperEvents(unittest.TestCase):

    def setUp(self):
        self.valid_timestamp = datetime(
            2026, 11, 4, 10, 0, tzinfo=timezone.utc
        )

        self.df = pl.DataFrame([
            {
                "event_id": "E001",
                "developer_id": "DEV01",
                "source": "github",
                "event_type": "commit",
                "event_timestamp": self.valid_timestamp,
                "metadata": '{"branch": "main"}',
            },
            {
                "event_id": "E002",
                "developer_id": "DEV02",
                "source": "jira",
                "event_type": "issue_created",
                "event_timestamp": self.valid_timestamp,
                "metadata": '{"issue": "TASK-101"}',
            },
        ])

    def test_valid_events(self):
        cleaned, rejected, report = clean_developer_events(self.df)
        self.assertEqual(cleaned.height, 2)
        self.assertEqual(rejected.height, 0)
        self.assertEqual(report["accepted_records"], 2)

    def test_duplicate_event_ids(self):
        df = pl.concat([self.df, self.df.head(1)])
        cleaned, rejected, report = clean_developer_events(df)
        self.assertEqual(cleaned.height, 2)
        self.assertEqual(rejected.height, 1)
        self.assertEqual(report["duplicate_records"], 1)

    def test_unsupported_source(self):
        df = self.df.with_columns(
            pl.when(pl.col("event_id") == "E001")
            .then(pl.lit("unknown"))
            .otherwise(pl.col("source"))
            .alias("source")
        )

        cleaned, rejected, report = clean_developer_events(df)
        self.assertEqual(cleaned.height, 1)
        self.assertEqual(rejected.height, 1)
        self.assertEqual(
            rejected["rejection_reason"][0],
            "unsupported_source"
        )

    def test_blank_developer_id(self):
        df = self.df.with_columns(
            pl.when(pl.col("event_id") == "E001")
            .then(pl.lit(""))
            .otherwise(pl.col("developer_id"))
            .alias("developer_id")
        )

        cleaned, rejected, report = clean_developer_events(df)
        self.assertEqual(cleaned.height, 1)
        self.assertEqual(rejected.height, 1)

    def test_invalid_timestamp(self):
        df = self.df.with_columns(
            pl.when(pl.col("event_id") == "E001")
            .then(pl.lit("invalid-date"))
            .otherwise(
                pl.col("event_timestamp").cast(pl.String)
            )
            .alias("event_timestamp")
        )

        cleaned, rejected, report = clean_developer_events(df)
        self.assertEqual(cleaned.height, 1)
        self.assertEqual(rejected.height, 1)
        self.assertEqual(
            rejected["rejection_reason"][0],
            "invalid_event_timestamp"
        )

    def test_missing_columns(self):
        df = self.df.drop("metadata")

        with self.assertRaises(ValueError):
            clean_developer_events(df)

    def test_wrong_input_type(self):
        with self.assertRaises(TypeError):
            clean_developer_events([{"event_id": "E001"}])

    def test_empty_input(self):
        empty_df = self.df.head(0)

        cleaned, rejected, report = clean_developer_events(empty_df)

        self.assertEqual(cleaned.height, 0)
        self.assertEqual(rejected.height, 0)
        self.assertEqual(report["total_records"], 0)


if __name__ == "__main__":
    unittest.main()
