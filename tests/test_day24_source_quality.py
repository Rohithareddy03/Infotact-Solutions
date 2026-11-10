from src.ingestion.quality_checks import validate_event_batch


def make_event(
    event_id="event_001",
    source="github",
    timestamp="2026-11-02T09:00:00+00:00",
):
    return {
        "event_id": event_id,
        "developer_id": "dev_001",
        "source": source,
        "event_type": "commit",
        "event_timestamp": timestamp,
        "metadata": {"repository": "cognistream"},
    }


def test_source_quality_tracks_accepted_events():
    report = validate_event_batch([
        make_event("gh_001", "github"),
        make_event("gh_002", "github"),
        make_event("sl_001", "slack"),
    ])

    assert report["source_quality"]["github"]["total_events"] == 2
    assert report["source_quality"]["github"]["accepted_events"] == 2
    assert report["source_quality"]["slack"]["accepted_events"] == 1


def test_source_quality_tracks_invalid_events():
    report = validate_event_batch([
        make_event("gh_001", "github"),
        make_event("gh_002", "github", timestamp="invalid"),
    ])

    github = report["source_quality"]["github"]

    assert github["total_events"] == 2
    assert github["accepted_events"] == 1
    assert github["invalid_events"] == 1
    assert github["rejected_events"] == 1
    assert "Invalid event_timestamp format." in github["error_reasons"]


def test_source_quality_tracks_duplicate_events():
    report = validate_event_batch([
        make_event("gh_001", "github"),
        make_event("gh_001", "github"),
    ])

    github = report["source_quality"]["github"]

    assert github["total_events"] == 2
    assert github["accepted_events"] == 1
    assert github["duplicate_events"] == 1
    assert github["rejected_events"] == 1
    assert github["error_reasons"]["Duplicate event_id."] == 1


def test_source_quality_groups_unsupported_sources_as_unknown():
    report = validate_event_batch([
        make_event("other_001", "unknown_source"),
    ])

    unknown = report["source_quality"]["unknown"]

    assert unknown["total_events"] == 1
    assert unknown["accepted_events"] == 0
    assert unknown["invalid_events"] == 1
    assert unknown["rejected_events"] == 1
    assert "Unsupported event source." in unknown["error_reasons"]


def test_source_quality_groups_missing_sources_as_unknown():
    event = make_event("missing_001")
    del event["source"]

    report = validate_event_batch([event])
    unknown = report["source_quality"]["unknown"]

    assert unknown["total_events"] == 1
    assert unknown["invalid_events"] == 1
    assert unknown["rejected_events"] == 1
    assert any(
        reason.startswith("Missing fields:")
        for reason in unknown["error_reasons"]
    )


def test_source_quality_keeps_all_source_categories():
    report = validate_event_batch([])

    assert set(report["source_quality"]) == {
        "github",
        "jira",
        "slack",
        "activitywatch",
        "unknown",
    }
