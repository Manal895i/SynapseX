"""
Unit tests for ADEIP Timeline Agent (Deterministic Chronological Reconstruction & Sequencing).
"""
import datetime
import pytest
from app.agents.state import InvestigationState
from app.agents.timeline_agent import (
    cluster_events_by_window,
    detect_deterministic_sequences,
    parse_and_normalize_timestamp,
    timeline_agent,
)


def test_timestamp_normalization_and_preservation():
    """Verify UTC normalization and preservation of original timestamp representation."""
    raw_iso_z = "2026-08-20T14:30:00Z"
    dt_utc, orig = parse_and_normalize_timestamp(raw_iso_z)
    assert dt_utc is not None
    assert dt_utc.tzinfo == datetime.timezone.utc
    assert dt_utc.hour == 14
    assert orig == raw_iso_z

    raw_offset = "2026-08-20T10:00:00+02:00"
    dt_utc2, orig2 = parse_and_normalize_timestamp(raw_offset)
    assert dt_utc2 is not None
    # 10:00 +02:00 -> 08:00 UTC
    assert dt_utc2.hour == 8
    assert orig2 == raw_offset


def test_time_window_clustering():
    """Events occurring within 5-minute window (300s) should form a single cluster."""
    base_time = datetime.datetime(2026, 8, 20, 10, 0, 0, tzinfo=datetime.timezone.utc)

    events = [
        {"event_id": 1, "evidence_id": 10, "timestamp_utc": base_time, "event_type": "cctv_entry"},
        {"event_id": 2, "evidence_id": 10, "timestamp_utc": base_time + datetime.timedelta(minutes=1), "event_type": "access_card"},
        {"event_id": 3, "evidence_id": 11, "timestamp_utc": base_time + datetime.timedelta(minutes=2), "event_type": "system_login"},
        {"event_id": 4, "evidence_id": 12, "timestamp_utc": base_time + datetime.timedelta(minutes=3), "event_type": "usb_connected"},
        # Event 5 is 30 minutes later -> separate cluster
        {"event_id": 5, "evidence_id": 12, "timestamp_utc": base_time + datetime.timedelta(minutes=30), "event_type": "file_exfiltrated"},
    ]

    clusters = cluster_events_by_window(events, window_seconds=300)
    assert len(clusters) == 2
    assert clusters[0]["event_count"] == 4
    assert clusters[1]["event_count"] == 1
    assert clusters[0]["evidence_ids"] == [10, 11, 12] or set(clusters[0]["evidence_ids"]) == {10, 11, 12}


def test_deterministic_sequence_detection():
    """Verify sequence detection across distinct evidence sources with non-causation disclaimer."""
    base_time = datetime.datetime(2026, 8, 20, 10, 0, 0, tzinfo=datetime.timezone.utc)

    events = [
        {"event_id": 1, "evidence_id": 10, "timestamp_utc": base_time, "event_type": "cctv_entry"},
        {"event_id": 2, "evidence_id": 11, "timestamp_utc": base_time + datetime.timedelta(seconds=60), "event_type": "badge_swipe"},
        {"event_id": 3, "evidence_id": 12, "timestamp_utc": base_time + datetime.timedelta(seconds=120), "event_type": "host_logon"},
    ]

    sequences = detect_deterministic_sequences(events, max_gap_seconds=300)
    assert len(sequences) >= 1
    seq = sequences[0]

    assert len(seq["evidence_ids"]) >= 2
    assert "causation" in seq["disclaimer"].lower()
    assert seq["time_span_seconds"] == 120.0


def test_timeline_agent_distinguishes_observed_from_hypothetical():
    """
    Timeline Agent must return observed factual events, time clusters,
    and possible sequences, keeping them strictly distinct.
    """
    mock_state: InvestigationState = {
        "case_id": 42,
        "evidence_ids": [1, 2],
        "event_ids": [101, 102, 103, 104],
        "case_info": {"id": 42, "title": "Operation Nightshade"},
        "evidence_items": [
            {"id": 1, "original_filename": "physical_access.csv"},
            {"id": 2, "original_filename": "workstation_security.json"},
        ],
        "raw_events": [
            {
                "id": 101,
                "evidence_id": 1,
                "event_type": "cctv_entry",
                "timestamp": "2026-08-20T10:02:00Z",
                "source": "physical_access.csv",
                "entity_type": "person",
                "entity_value": "Employee 9021",
            },
            {
                "id": 102,
                "evidence_id": 1,
                "event_type": "badge_swipe",
                "timestamp": "2026-08-20T10:03:00Z",
                "source": "physical_access.csv",
                "entity_type": "user_account",
                "entity_value": "sec_badge_88",
            },
            {
                "id": 103,
                "evidence_id": 2,
                "event_type": "system_login",
                "timestamp": "2026-08-20T10:04:00Z",
                "source": "workstation_security.json",
                "entity_type": "user_account",
                "entity_value": "admin_ops",
            },
            {
                "id": 104,
                "evidence_id": 2,
                "event_type": "usb_connected",
                "timestamp": "2026-08-20T10:05:00Z",
                "source": "workstation_security.json",
                "entity_type": "usb_device",
                "entity_value": "USBSTOR\\Disk&Ven_SanDisk",
            },
        ],
        "extracted_entities": [],
        "agent_logs": [],
    }

    result = timeline_agent(mock_state)

    observed = result["timeline"]
    clusters = result["time_clusters"]
    sequences = result["possible_sequences"]

    # 1. Observed events
    assert len(observed) == 4
    assert observed[0]["event_type"] == "cctv_entry"
    assert observed[1]["event_type"] == "badge_swipe"
    assert observed[2]["event_type"] == "system_login"
    assert observed[3]["event_type"] == "usb_connected"

    # 2. Clusters (all 4 occurred within 3 minutes -> 1 cluster)
    assert len(clusters) == 1
    assert clusters[0]["event_count"] == 4

    # 3. Possible sequences detected across physical_access & workstation_security
    assert len(sequences) >= 1
    for s in sequences:
        assert "disclaimer" in s
        assert "not automatically establish causation" in s["disclaimer"]
