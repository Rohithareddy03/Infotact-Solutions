
"""Tests for Day 25 pipeline monitoring reliability."""

import json
import tempfile
import unittest
from pathlib import Path

from src.processing.pipeline_observability import run_monitored_pipeline


class TestDay25PipelineReliability(unittest.TestCase):

    def test_non_dictionary_result_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            def pipeline():
                return ["invalid", "result"]

            with self.assertRaisesRegex(
                RuntimeError,
                "Pipeline failed: Pipeline function must return a dictionary.",
            ):
                run_monitored_pipeline(
                    pipeline,
                    report_dir=temp_dir,
                )

            reports = list(Path(temp_dir).glob("*.json"))
            self.assertEqual(len(reports), 1)

            with reports[0].open(encoding="utf-8") as file:
                report = json.load(file)

            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["error"]["type"], "TypeError")

    def test_invalid_status_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            def pipeline():
                return {
                    "status": "invalid_status",
                    "input_events": 10,
                }

            with self.assertRaisesRegex(
                RuntimeError,
                "Pipeline failed: Pipeline returned an invalid status",
            ):
                run_monitored_pipeline(
                    pipeline,
                    report_dir=temp_dir,
                )

            reports = list(Path(temp_dir).glob("*.json"))
            self.assertEqual(len(reports), 1)

            with reports[0].open(encoding="utf-8") as file:
                report = json.load(file)

            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["error"]["type"], "ValueError")
            self.assertIn(
                "invalid_status",
                report["error"]["message"],
            )

    def test_success_status_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            def pipeline():
                return {
                    "status": "success",
                    "input_events": 10,
                    "analytics_records": 8,
                    "inserted_records": 8,
                }

            result = run_monitored_pipeline(
                pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(result["report"]["status"], "success")
            self.assertEqual(result["result"]["input_events"], 10)

    def test_no_data_status_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            def pipeline():
                return {
                    "status": "no_data",
                    "input_events": 0,
                    "analytics_records": 0,
                    "inserted_records": 0,
                }

            result = run_monitored_pipeline(
                pipeline,
                report_dir=temp_dir,
            )

            self.assertEqual(result["report"]["status"], "no_data")


if __name__ == "__main__":
    unittest.main()
