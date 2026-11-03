import json
import tempfile
import unittest

from pathlib import Path

from src.processing.pipeline_observability import (
    run_monitored_pipeline,
    save_observability_report,
)


def successful_pipeline():
    return {
        "input_events": 40,
        "analytics_records": 5,
        "inserted_records": 5,
        "status": "success",
    }


def empty_pipeline():
    return {
        "input_events": 0,
        "analytics_records": 0,
        "inserted_records": 0,
        "status": "no_data",
    }


def failing_pipeline():
    raise ValueError("Simulated database connection failure")


class TestPipelineObservability(unittest.TestCase):

    def test_successful_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_monitored_pipeline(
                successful_pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(
                output["report"]["status"],
                "success",
            )

            self.assertEqual(
                output["report"]["metrics"]["input_events"],
                40,
            )

    def test_result_is_returned(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_monitored_pipeline(
                successful_pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(
                output["result"]["inserted_records"],
                5,
            )

    def test_report_file_is_created(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_monitored_pipeline(
                successful_pipeline,
                report_dir=temp_dir,
            )

            report_path = Path(
                output["report"]["report_path"]
            )

            self.assertTrue(report_path.exists())

    def test_saved_report_contains_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_monitored_pipeline(
                successful_pipeline,
                report_dir=temp_dir,
            )

            with open(
                output["report"]["report_path"],
                encoding="utf-8",
            ) as file:
                saved_report = json.load(file)

            self.assertEqual(
                saved_report["metrics"]["inserted_records"],
                5,
            )

    def test_metadata_is_saved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = {
                "dag_id": "cognistream_analytics",
                "ingestion_quality": {
                    "total_events": 40,
                    "valid_events": 38,
                    "invalid_events": 2,
                },
            }

            output = run_monitored_pipeline(
                successful_pipeline,
                report_dir=temp_dir,
                report_metadata=metadata,
            )

            with open(
                output["report"]["report_path"],
                encoding="utf-8",
            ) as file:
                saved_report = json.load(file)

            self.assertEqual(
                saved_report["metadata"]["ingestion_quality"][
                    "invalid_events"
                ],
                2,
            )

    def test_failed_pipeline_records_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(RuntimeError):
                run_monitored_pipeline(
                    failing_pipeline,
                    report_dir=temp_dir,
                )

            report_files = list(Path(temp_dir).glob("*.json"))
            self.assertEqual(len(report_files), 1)

            with report_files[0].open(
                encoding="utf-8"
            ) as file:
                report = json.load(file)

            self.assertEqual(report["status"], "failed")
            self.assertEqual(
                report["error"]["type"],
                "ValueError",
            )

    def test_failure_message_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(RuntimeError):
                run_monitored_pipeline(
                    failing_pipeline,
                    report_dir=temp_dir,
                )

            report_files = list(Path(temp_dir).glob("*.json"))

            with report_files[0].open(
                encoding="utf-8"
            ) as file:
                report = json.load(file)

            self.assertIn(
                "database connection failure",
                report["error"]["message"],
            )

    def test_no_data_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_monitored_pipeline(
                empty_pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(
                output["report"]["status"],
                "no_data",
            )

    def test_duration_is_recorded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = run_monitored_pipeline(
                successful_pipeline,
                report_dir=temp_dir,
            )

            self.assertIsInstance(
                output["report"]["duration_seconds"],
                float,
            )

            self.assertGreaterEqual(
                output["report"]["duration_seconds"],
                0,
            )

    def test_manual_report_saving(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report = {
                "run_id": "test-run-001",
                "status": "success",
            }

            path = save_observability_report(
                report,
                temp_dir,
            )

            self.assertTrue(Path(path).exists())


if __name__ == "__main__":
    unittest.main()