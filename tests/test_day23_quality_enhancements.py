from src.ingestion.quality_checks import validate_event_batch


def make_event(event_id="event_001", source="github"):
    return {
        "event_id": event_id,
        "developer_id": "dev_001",
        "source": source,
        "event_type": "commit",
        "event_timestamp": "2026-11-02T09:00:00+00:00",
        "metadata": {"repository": "cognistream"},
    }


def test_source_is_normalized_to_lowercase():
    report = validate_event_batch([
        make_event(source=" GITHUB ")
    ])

    assert report["accepted_events"] == 1
    assert report["valid_events"][0]["source"] == "github"


def test_duplicate_records_are_reported_as_rejected():
    report = validate_event_batch([
        make_event("event_001"),
        make_event("event_001"),
        make_event("event_002"),
    ])

    assert report["accepted_events"] == 2
    assert report["rejected_events"] == 1
    assert report["duplicate_extra_rows"] == 1
    assert report["duplicate_events"][0]["index"] == 1
    assert report["duplicate_events"][0]["event_id"] == "event_001"


def test_duplicate_ids_are_reported_once():
    report = validate_event_batch([
        make_event("event_001"),
        make_event("event_001"),
        make_event("event_001"),
    ])

    assert report["duplicate_event_ids"] == ["event_001"]
    assert report["duplicate_extra_rows"] == 2
    assert report["rejected_events"] == 2
