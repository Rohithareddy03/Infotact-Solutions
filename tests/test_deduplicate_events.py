"""Tests for developer event deduplication."""

import unittest

import polars as pl

from src.processing.deduplicate_events import deduplicate_events


class TestDeduplicateEvents(unittest.TestCase):

    def setUp(self):
        self.df = pl.DataFrame(
            {
                "event_id": ["e1", "e2", "e1", "e3", "e2"],
                "developer_id": [
                    "dev1", "dev2", "dev1", "dev3", "dev2"
                ],
                "source": [
                    "github", "jira", "github", "slack", "jira"
                ],
            }
        )

    def test_removes_duplicate_events(self):
        result, removed = deduplicate_events(self.df)

        self.assertEqual(result.height, 3)
        self.assertEqual(removed, 2)

    def test_keeps_first_occurrence(self):
        result, _ = deduplicate_events(self.df)

        self.assertEqual(
            result.get_column("event_id").to_list(),
            ["e1", "e2", "e3"],
        )

    def test_preserves_original_column_names(self):
        result, _ = deduplicate_events(self.df)

        self.assertEqual(result.columns, self.df.columns)

    def test_no_duplicates(self):
        df = pl.DataFrame(
            {
                "event_id": ["e1", "e2"],
                "source": ["github", "jira"],
            }
        )

        result, removed = deduplicate_events(df)

        self.assertEqual(result.height, 2)
        self.assertEqual(removed, 0)

    def test_empty_dataframe(self):
        df = pl.DataFrame(
            schema={
                "event_id": pl.String,
                "source": pl.String,
            }
        )

        result, removed = deduplicate_events(df)

        self.assertEqual(result.height, 0)
        self.assertEqual(removed, 0)

    def test_missing_event_id_column(self):
        df = pl.DataFrame({"source": ["github"]})

        with self.assertRaises(ValueError):
            deduplicate_events(df)

    def test_invalid_input_type(self):
        with self.assertRaises(TypeError):
            deduplicate_events([{"event_id": "e1"}])


if __name__ == "__main__":
    unittest.main()