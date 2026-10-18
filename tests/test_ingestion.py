
import unittest

from src.ingestion.mock_events import generate_mock_events
from src.ingestion.validation import validate_event, validate_events


class TestIngestion(unittest.TestCase):

    def test_generate_requested_number_of_events(self):
        events = generate_mock_events(12)
        self.assertEqual(len(events), 12)

    def test_event_ids_are_unique(self):
        events = generate_mock_events(20)
        ids = [event["event_id"] for event in events]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_sources_are_represented(self):
        events = generate_mock_events(4)
        sources = {event["source"] for event in events}

        self.assertEqual(
            sources,
            {"github", "jira", "slack", "activitywatch"},
        )

    def test_valid_event_is_accepted(self):
        event = generate_mock_events(1)[0]
        valid, message = validate_event(event)

        self.assertTrue(valid, message)

    def test_missing_field_is_rejected(self):
        event = generate_mock_events(1)[0]
        event.pop("developer_id")

        valid, message = validate_event(event)

        self.assertFalse(valid)
        self.assertIn("Missing fields", message)

    def test_invalid_source_is_rejected(self):
        event = generate_mock_events(1)[0]
        event["source"] = "unknown"

        valid, _ = validate_event(event)
        self.assertFalse(valid)

    def test_timezone_is_required(self):
        event = generate_mock_events(1)[0]
        event["event_timestamp"] = "2026-10-18T10:30:00"

        valid, message = validate_event(event)

        self.assertFalse(valid)
        self.assertIn("timezone", message)

    def test_valid_and_invalid_events_are_separated(self):
        valid_event = generate_mock_events(1)[0]
        invalid_event = dict(valid_event)
        invalid_event["event_id"] = "invalid-event"
        invalid_event["source"] = "unknown"

        valid, invalid = validate_events(
            [valid_event, invalid_event]
        )

        self.assertEqual(len(valid), 1)
        self.assertEqual(len(invalid), 1)


if __name__ == "__main__":
    unittest.main()
