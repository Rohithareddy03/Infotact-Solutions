"""Tests for the CogniStream analytics export pipeline."""

import unittest
from unittest.mock import MagicMock, patch

import polars as pl

from src.processing.analytics_pipeline import (
    build_analytics_records,
    export_analytics_to_clickhouse,
)


SAMPLE_EVENTS = [
    {
        "event_id": "event_001",
        "developer_id": "dev_001",
        "source": "github",
        "event_type": "commit",
        "event_timestamp": "2026-10-29T09:00:00+00:00",
        "metadata": {"repository": "cognistream"},
    }
]

SAMPLE_RECORDS = [
    {
        "snapshot_date": "2026-10-29",
        "developer_id": "dev_001",
        "total_events": 1,
    }
]


class TestBuildAnalyticsRecords(unittest.TestCase):

    def test_empty_events_return_empty_records(self):
        result = build_analytics_records([], "2026-10-29")
        self.assertEqual(result, [])

    def test_non_list_events_are_rejected(self):
        with self.assertRaises(TypeError):
            build_analytics_records("invalid", "2026-10-29")

    def test_non_dictionary_event_is_rejected(self):
        with self.assertRaises(ValueError):
            build_analytics_records(
                [SAMPLE_EVENTS[0], "invalid"],
                "2026-10-29",
            )

    def test_negative_inactivity_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            build_analytics_records(
                SAMPLE_EVENTS,
                "2026-10-29",
                inactivity_threshold_minutes=-1,
            )

    @patch(
        "src.processing.analytics_pipeline.prepare_clickhouse_records"
    )
    @patch(
        "src.processing.analytics_pipeline.build_unified_analytics"
    )
    @patch(
        "src.processing.analytics_pipeline.detect_activity_blocks"
    )
    @patch(
        "src.processing.analytics_pipeline.analyze_context_switches"
    )
    @patch(
        "src.processing.analytics_pipeline.calculate_developer_metrics"
    )
    @patch("src.processing.analytics_pipeline.transform_events")
    def test_processing_steps_are_connected(
        self,
        mock_transform,
        mock_activity_metrics,
        mock_context_metrics,
        mock_blocks,
        mock_unified,
        mock_export,
    ):
        events_df = pl.DataFrame(
            {
                "developer_id": ["dev_001"],
                "source": ["github"],
                "event_type": ["commit"],
                "event_timestamp": [
                    "2026-10-29T09:00:00+00:00"
                ],
            }
        )

        activity_df = pl.DataFrame({"developer_id": ["dev_001"]})
        context_df = pl.DataFrame({"developer_id": ["dev_001"]})
        blocks_df = pl.DataFrame({"developer_id": ["dev_001"]})
        unified_df = pl.DataFrame({"developer_id": ["dev_001"]})

        mock_transform.return_value = events_df
        mock_activity_metrics.return_value = activity_df
        mock_context_metrics.return_value = context_df
        mock_blocks.return_value = blocks_df
        mock_unified.return_value = unified_df
        mock_export.return_value = SAMPLE_RECORDS

        result = build_analytics_records(
            SAMPLE_EVENTS,
            "2026-10-29",
        )

        self.assertEqual(result, SAMPLE_RECORDS)
        mock_transform.assert_called_once_with(SAMPLE_EVENTS)
        mock_activity_metrics.assert_called_once_with(events_df)
        mock_context_metrics.assert_called_once_with(events_df)
        mock_blocks.assert_called_once_with(
            events_df,
            inactivity_threshold_minutes=15,
        )
        mock_unified.assert_called_once_with(
            activity_df,
            context_df,
            blocks_df,
        )
        mock_export.assert_called_once_with(
            unified_df,
            snapshot_date="2026-10-29",
        )


class TestExportAnalyticsToClickHouse(unittest.TestCase):

    @patch(
        "src.processing.analytics_pipeline.build_analytics_records"
    )
    @patch(
        "src.processing.analytics_pipeline.insert_developer_analytics"
    )
    def test_export_inserts_prepared_records(
        self,
        mock_insert,
        mock_build,
    ):
        mock_build.return_value = SAMPLE_RECORDS
        mock_insert.return_value = 1
        client = MagicMock()

        result = export_analytics_to_clickhouse(
            SAMPLE_EVENTS,
            "2026-10-29",
            client=client,
        )

        self.assertEqual(
            result,
            {
                "input_events": 1,
                "analytics_records": 1,
                "inserted_records": 1,
                "status": "success",
            },
        )

        mock_insert.assert_called_once_with(client, SAMPLE_RECORDS)

    @patch(
        "src.processing.analytics_pipeline.build_analytics_records"
    )
    @patch(
        "src.processing.analytics_pipeline.create_clickhouse_client"
    )
    @patch(
        "src.processing.analytics_pipeline.insert_developer_analytics"
    )
    def test_client_is_created_when_not_supplied(
        self,
        mock_insert,
        mock_create_client,
        mock_build,
    ):
        mock_build.return_value = SAMPLE_RECORDS
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_insert.return_value = 1

        export_analytics_to_clickhouse(
            SAMPLE_EVENTS,
            "2026-10-29",
        )

        mock_create_client.assert_called_once_with()
        mock_insert.assert_called_once_with(
            mock_client,
            SAMPLE_RECORDS,
        )

    @patch(
        "src.processing.analytics_pipeline.build_analytics_records"
    )
    @patch(
        "src.processing.analytics_pipeline.create_clickhouse_client"
    )
    @patch(
        "src.processing.analytics_pipeline.insert_developer_analytics"
    )
    def test_empty_records_skip_database_connection(
        self,
        mock_insert,
        mock_create_client,
        mock_build,
    ):
        mock_build.return_value = []

        result = export_analytics_to_clickhouse(
            [],
            "2026-10-29",
        )

        self.assertEqual(result["status"], "no_data")
        self.assertEqual(result["inserted_records"], 0)
        mock_create_client.assert_not_called()
        mock_insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()