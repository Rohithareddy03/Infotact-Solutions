
"""Tests for developer event data-quality checks."""

import unittest

import polars as pl

from src.processing.data_quality import generate_quality_report


class TestDataQuality(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame({
            "event_id": ["event-1", "event-2"],
            "developer_id": ["dev-1", "dev-2"],
            "source": ["github", "jira"],
            "event_type": ["commit", "issue"],
            "event_timestamp": [
                "2026-10-19T10:00:00+00:00",
                "2026-10-19T11:00:00+00:00",
            ],
            "metadata": ['{"repo":"demo"}', '{"issue":1}'],
        })

    def test_clean_data_is_valid(self):
        report = generate_quality_report(self.df)

        self.assertTrue(report["is_valid"])
        self.assertEqual(report["total_rows"], 2)
        self.assertEqual(report["duplicate_event_ids"], [])

    def test_duplicate_ids_are_detected(self):
        df = pl.concat([self.df, self.df.slice(0, 1)])
        report = generate_quality_report(df)

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["duplicate_event_ids"], ["event-1"])
        self.assertEqual(report["duplicate_extra_rows"], 1)

    def test_null_values_are_detected(self):
        df = self.df.with_columns(
            pl.Series("developer_id", ["dev-1", None])
        )
        report = generate_quality_report(df)

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["null_counts"]["developer_id"], 1)

    def test_empty_strings_are_detected(self):
        df = self.df.with_columns(
            pl.Series("source", ["github", "  "])
        )
        report = generate_quality_report(df)

        self.assertFalse(report["is_valid"])
        self.assertEqual(report["empty_string_counts"]["source"], 1)

    def test_missing_required_column_raises_error(self):
        df = self.df.drop("developer_id")

        with self.assertRaises(ValueError):
            generate_quality_report(df)

    def test_empty_dataframe_is_valid(self):
        empty_df = self.df.head(0)
        report = generate_quality_report(empty_df)

        self.assertTrue(report["is_valid"])
        self.assertEqual(report["total_rows"], 0)


if __name__ == "__main__":
    unittest.main()
