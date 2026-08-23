"""
Unit tests for ADEIP Correlation Agent (Explainable Multi-Signal Correlation Engine).
"""
import pytest
from app.agents.correlation_agent import correlation_agent
from app.agents.state import InvestigationState


@pytest.fixture
def multi_signal_case_state() -> InvestigationState:
    """Fixture with cross-evidence events and shared entities."""
    return {
        "case_id": 99,
        "evidence_ids": [1, 2],
        "event_ids": [101, 102, 103, 104],
        "case_info": {"id": 99, "title": "Corporate Espionage Case"},
        "evidence_items": [
            {"id": 1, "original_filename": "perimeter_firewall.csv", "sha256_hash": "aaa111"},
            {"id": 2, "original_filename": "ad_security_logs.json", "sha256_hash": "bbb222"},
        ],
        "extracted_entities": [
            # Shared IP across Evidence 1 & 2
            {
                "id": 1,
                "entity_type": "ip_address",
                "entity_value": "198.51.100.45",
                "normalized_value": "198.51.100.45",
                "evidence_id": 1,
                "event_ids": [101],
            },
            {
                "id": 2,
                "entity_type": "ip_address",
                "entity_value": "198.51.100.45",
                "normalized_value": "198.51.100.45",
                "evidence_id": 2,
                "event_ids": [102],
            },
            # Shared User across Evidence 1 & 2
            {
                "id": 3,
                "entity_type": "user_account",
                "entity_value": "v_suspect@adeip.internal",
                "normalized_value": "v_suspect@adeip.internal",
                "evidence_id": 1,
                "event_ids": [101],
            },
            {
                "id": 4,
                "entity_type": "user_account",
                "entity_value": "v_suspect@adeip.internal",
                "normalized_value": "v_suspect@adeip.internal",
                "evidence_id": 2,
                "event_ids": [102],
            },
            # Device
            {
                "id": 5,
                "entity_type": "device",
                "entity_value": "WS-EXFIL-09",
                "normalized_value": "WS-EXFIL-09",
                "evidence_id": 2,
                "event_ids": [102, 103],
            },
            # Shared File
            {
                "id": 6,
                "entity_type": "file",
                "entity_value": "confidential_patent.pdf",
                "normalized_value": "confidential_patent.pdf",
                "evidence_id": 1,
                "event_ids": [104],
            },
            {
                "id": 7,
                "entity_type": "file",
                "entity_value": "confidential_patent.pdf",
                "normalized_value": "confidential_patent.pdf",
                "evidence_id": 2,
                "event_ids": [103],
            },
        ],
        "raw_events": [
            {"id": 101, "evidence_id": 1, "event_type": "traffic_outbound", "timestamp": "2026-08-20T10:00:00Z"},
            {"id": 102, "evidence_id": 2, "event_type": "auth_success", "timestamp": "2026-08-20T10:02:00Z"},
            {"id": 103, "evidence_id": 2, "event_type": "usb_file_copy", "timestamp": "2026-08-20T10:03:00Z"},
            {"id": 104, "evidence_id": 1, "event_type": "upload_detected", "timestamp": "2026-08-20T10:04:00Z"},
        ],
        "timeline": [
            {"event_id": 101, "evidence_id": 1, "event_type": "traffic_outbound", "timestamp_utc": "2026-08-20T10:00:00+00:00", "entities": ["ip:198.51.100.45"]},
            {"event_id": 102, "evidence_id": 2, "event_type": "auth_success", "timestamp_utc": "2026-08-20T10:02:00+00:00", "entities": ["user:v_suspect"]},
            {"event_id": 103, "evidence_id": 2, "event_type": "usb_file_copy", "timestamp_utc": "2026-08-20T10:03:00+00:00", "entities": ["file:confidential_patent.pdf"]},
            {"event_id": 104, "evidence_id": 1, "event_type": "upload_detected", "timestamp_utc": "2026-08-20T10:04:00+00:00", "entities": ["file:confidential_patent.pdf"]},
        ],
        "agent_logs": [],
    }


def test_correlation_agent_signals_detected(multi_signal_case_state):
    """Correlation agent should identify all key explainable correlation signals."""
    result = correlation_agent(multi_signal_case_state)
    correlations = result["correlations"]

    assert len(correlations) >= 4

    signal_types = {c["signal_type"] for c in correlations}
    assert "same_ip_address" in signal_types
    assert "same_user_account" in signal_types
    assert "same_device" in signal_types
    assert "same_file" in signal_types
    assert "timestamp_proximity" in signal_types or "multi_signal_convergence" in signal_types


def test_correlation_contains_all_required_attributes(multi_signal_case_state):
    """Every correlation must contain all requested fields and explainable reasons."""
    result = correlation_agent(multi_signal_case_state)
    correlations = result["correlations"]

    for c in correlations:
        # Check required keys
        assert "correlation_id" in c
        assert c["correlation_id"].startswith("CORR-99-")
        assert "signal_type" in c
        assert "title" in c
        assert "description" in c
        assert "correlation_score" in c
        assert 0.0 <= c["correlation_score"] <= 1.0
        assert "related_event_ids" in c
        assert "supporting_evidence_ids" in c
        assert "reasons" in c
        assert isinstance(c["reasons"], list)
        assert len(c["reasons"]) >= 1

        # Check explainability: reason must not be blank
        for r in c["reasons"]:
            assert len(r.strip()) > 5


def test_correlation_non_proof_wording_and_disclaimer(multi_signal_case_state):
    """
    CRITICAL REQUIREMENT:
    Correlations must never claim proof or declare guilt.
    Must use wording such as 'Potential relationship detected' and include disclaimer.
    """
    result = correlation_agent(multi_signal_case_state)
    correlations = result["correlations"]

    for c in correlations:
        assert "Potential relationship detected" in c["title"] or "Potential relationship detected" in c["description"] or "Potential relationship detected" in " ".join(c["reasons"])
        assert "disclaimer" in c
        assert "not establish causation" in c["disclaimer"]
        assert "proof" in c["disclaimer"]
