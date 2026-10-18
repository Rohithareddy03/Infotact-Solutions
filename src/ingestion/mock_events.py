
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import json
from pathlib import Path


SOURCES = {
    "github": ["commit", "pull_request"],
    "jira": ["issue_created", "issue_updated", "status_changed"],
    "slack": ["notification"],
    "activitywatch": ["ide_activity", "application_switch"],
}


def generate_mock_events(count: int = 40) -> list[dict]:
    """Generate simulated developer activity events."""
    if count < 0:
        raise ValueError("count cannot be negative")

    events = []
    now = datetime.now(timezone.utc)

    source_names = list(SOURCES)

    for i in range(count):
        source = source_names[i % len(source_names)]
        event_type = SOURCES[source][i % len(SOURCES[source])]
        timestamp = now - timedelta(minutes=i * 5)

        event = {
            "event_id": str(uuid4()),
            "developer_id": f"dev_{(i % 4) + 1:03d}",
            "source": source,
            "event_type": event_type,
            "event_timestamp": timestamp.isoformat(),
            "metadata": {
                "simulated": True,
                "sequence": i + 1,
            },
        }

        events.append(event)

    return events


def save_events(events: list[dict], output_path: str) -> None:
    """Save events as a JSON array."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=2)


if __name__ == "__main__":
    output_file = "data/sample/developer_events.json"
    sample_events = generate_mock_events(40)
    save_events(sample_events, output_file)

    print(f"Generated {len(sample_events)} simulated events.")
    print(f"Saved events to: {output_file}")
