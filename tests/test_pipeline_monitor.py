"""Tests for CogniStream pipeline monitoring."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.processing.pipeline_monitor import (
    create_execution_report,
    monitor_pipeline,
    save_execution_report,
)


class TestCreateExecutionReport(unittest.TestCase):

    def test_success_report(self):
        report = create_execution_report(
            input_events=100,
            analytics_records=5,
            inserted_records=5,
            status="success",
            duration_seconds=2.45678,
        )

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["input_events"], 100)
        self.assertEqual(report["analytics_records"], 5)
        self.assertEqual(report["inserted_records"], 5)
        self.assertEqual(report["duration_seconds"], 2.457)
        self.assertIsNone(report["error"])
        self.assertIn("+00:00", report["execution_time"])

    def test_no_data_report(self):
        report = create_execution_report(
            0, 0, 0, "no_data", 0.1
        )

        self.assertEqual(report["status"], "no_data")

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValueError):
            create_execution_report(1, 1, 1, "unknown", 1.0)

    def test_negative_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            create_execution_report(-1, 0, 0, "failed", 1.0)

    def test_negative_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            create_execution_report(1, 1, 1, "success", -1.0)


class TestSaveExecutionReport(unittest.TestCase):

    def test_report_is_saved_as_json(self):
        report = create_execution_report(
            10, 2, 2, "success", 1.25
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = save_execution_report(
                report, temp_dir
            )

            self.assertTrue(report_path.exists())

            with report_path.open(
                "r", encoding="utf-8"
            ) as file:
                saved_report = json.load(file)

            self.assertEqual(saved_report["status"], "success")
            self.assertEqual(saved_report["input_events"], 10)


class TestMonitorPipeline(unittest.TestCase):

    def test_successful_pipeline_is_monitored(self):
        pipeline_result = {
            "input_events": 20,
            "analytics_records": 2,
            "inserted_records": 2,
            "status": "success",
        }

        def fake_pipeline():
            return pipeline_result

        with tempfile.TemporaryDirectory() as temp_dir:
            report = monitor_pipeline(
                fake_pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(report["status"], "success")
            self.assertEqual(report["input_events"], 20)
            self.assertTrue(
                list(Path(temp_dir).glob("pipeline_report_*.json"))
            )

    def test_no_data_pipeline(self):
        def fake_pipeline():
            return {
                "input_events": 0,
                "analytics_records": 0,
                "inserted_records": 0,
                "status": "no_data",
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            report = monitor_pipeline(
                fake_pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(report["status"], "no_data")

    def test_failed_pipeline_saves_report_and_reraises(self):
        def failing_pipeline():
            raise RuntimeError("ClickHouse unavailable")

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                RuntimeError, "ClickHouse unavailable"
            ):
                monitor_pipeline(
                    failing_pipeline,
                    report_dir=temp_dir,
                )

            report_files = list(
                Path(temp_dir).glob("pipeline_report_*.json")
            )

            self.assertEqual(len(report_files), 1)

            with report_files[0].open(
                "r", encoding="utf-8"
            ) as file:
                saved_report = json.load(file)

            self.assertEqual(saved_report["status"], "failed")
            self.assertEqual(
                saved_report["error"],
                "ClickHouse unavailable",
            )

    def test_non_dictionary_result_is_rejected(self):
        def invalid_pipeline():
            return "invalid"

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                TypeError, "must return a dictionary"
            ):
                monitor_pipeline(
                    invalid_pipeline,
                    report_dir=temp_dir,
                )


if __name__ == "__main__":
    unittest.main()