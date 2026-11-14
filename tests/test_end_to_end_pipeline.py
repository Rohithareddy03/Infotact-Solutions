import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.ingestion.end_to_end_pipeline import (
    run_end_to_end_pipeline,
)
from src.ingestion.file_loader import load_events


class TestEndToEndPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.input_file = Path(self.temp_dir.name) / "events.json"
        self.input_file.write_text(
            '[{"event_id":"E001"}]',
            encoding="utf-8",
        )

        self.events = [
            {"event_id": "E001"},
            {"event_id": "E002"},
        ]

        self.quality_summary = {
            "total_events": 2,
            "valid_events": 2,
            "invalid_events": 0,
            "accepted_events": self.events,
            "rejected_events": [],
        }

        self.load_events = Mock(return_value=self.events)

        self.validate_event_batch = Mock(
            return_value=self.quality_summary
        )

        self.export_to_clickhouse = Mock(
            return_value={"status": "success", "inserted": 2}
        )

        self.monitor_pipeline = Mock(
            return_value={"monitoring_status": "completed"}
        )

    def run_pipeline(self):
        return run_end_to_end_pipeline(
            input_file=str(self.input_file),
            load_events=self.load_events,
            validate_event_batch=self.validate_event_batch,
            export_analytics_to_clickhouse=self.export_to_clickhouse,
            monitor_pipeline=self.monitor_pipeline,
        )

    def run_pipeline_with_real_loader(self):
        return run_end_to_end_pipeline(
            input_file=str(self.input_file),
            load_events=load_events,
            validate_event_batch=self.validate_event_batch,
            export_analytics_to_clickhouse=self.export_to_clickhouse,
            monitor_pipeline=self.monitor_pipeline,
        )

    def test_successful_pipeline(self):
        result = self.run_pipeline()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["total_events"], 2)
        self.assertEqual(result["accepted_events"], 2)

    def test_events_are_loaded(self):
        self.run_pipeline()

        self.load_events.assert_called_once_with(
            str(self.input_file)
        )

    def test_validation_receives_loaded_events(self):
        self.run_pipeline()

        self.validate_event_batch.assert_called_once_with(
            self.events
        )

    def test_only_accepted_events_are_exported(self):
        self.run_pipeline()

        kwargs = self.export_to_clickhouse.call_args.kwargs

        self.assertEqual(
            kwargs["accepted_events"],
            self.events,
        )

    def test_monitoring_runs_after_export(self):
        self.run_pipeline()

        self.export_to_clickhouse.assert_called_once()
        self.monitor_pipeline.assert_called_once()

    def test_partial_pipeline_when_events_are_rejected(self):
        self.quality_summary["rejected_events"] = [
            {"event": {"event_id": "E002"}, "reason": "invalid"}
        ]
        self.quality_summary["valid_events"] = 1
        self.quality_summary["invalid_events"] = 1
        self.quality_summary["accepted_events"] = [
            {"event_id": "E001"}
        ]

        result = self.run_pipeline()

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["rejected_events"], 1)

    def test_missing_input_file(self):
        with self.assertRaises(FileNotFoundError):
            run_end_to_end_pipeline(
                input_file=str(
                    Path(self.temp_dir.name) / "missing.json"
                ),
                load_events=self.load_events,
                validate_event_batch=self.validate_event_batch,
                export_analytics_to_clickhouse=self.export_to_clickhouse,
                monitor_pipeline=self.monitor_pipeline,
            )

    def test_invalid_quality_summary(self):
        self.validate_event_batch.return_value = {
            "total_events": 2
        }

        with self.assertRaises(ValueError):
            self.run_pipeline()

        self.export_to_clickhouse.assert_not_called()

    def test_export_failure_is_propagated(self):
        self.export_to_clickhouse.side_effect = RuntimeError(
            "ClickHouse export failed"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "ClickHouse export failed",
        ):
            self.run_pipeline()

        self.monitor_pipeline.assert_not_called()

    def test_invalid_json_stops_pipeline(self):
        self.input_file.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            self.run_pipeline_with_real_loader()

        self.validate_event_batch.assert_not_called()
        self.export_to_clickhouse.assert_not_called()
        self.monitor_pipeline.assert_not_called()

    def test_empty_file_stops_pipeline(self):
        self.input_file.write_text("", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "empty"):
            self.run_pipeline_with_real_loader()

        self.validate_event_batch.assert_not_called()
        self.export_to_clickhouse.assert_not_called()
        self.monitor_pipeline.assert_not_called()


if __name__ == "__main__":
    unittest.main()
