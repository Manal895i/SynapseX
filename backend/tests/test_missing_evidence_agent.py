"""
Unit tests for ADEIP Missing Evidence Agent (Gap Analysis & Advisory Acquisition Guidance).
"""
import pytest
from app.agents.missing_evidence_agent import missing_evidence_agent
from app.agents.state import InvestigationState
from app.models.recommendation import RecommendationPriority


@pytest.fixture
def gap_analysis_test_state() -> InvestigationState:
    """Fixture providing case state with clear timeline gaps, missing EVTX, and one-sided traffic."""
    return {
        "case_id": 55,
        "case_info": {"id": 55, "title": "Suspected Egress Exfiltration"},
        "evidence_items": [
            {"id": 1, "original_filename": "network_traffic.csv", "integrity_status": "unverified"},
        ],
        "raw_events": [
            {"id": 1, "evidence_id": 1, "event_type": "egress_traffic", "timestamp": "2026-08-20T10:00:00Z", "metadata": {"ip": "185.220.101.47"}},
            {"id": 2, "evidence_id": 1, "event_type": "egress_traffic", "timestamp": "2026-08-20T10:45:00Z", "metadata": {"ip": "185.220.101.47"}},
        ],
        "extracted_entities": [
            {"id": 1, "entity_type": "ip_address", "entity_value": "185.220.101.47", "evidence_id": 1, "event_ids": [1, 2]},
        ],
        "correlations": [],
        "timeline": [
            {"event_id": 1, "timestamp_utc": "2026-08-20T10:00:00Z", "event_type": "egress_traffic"},
            {"event_id": 2, "timestamp_utc": "2026-08-20T10:45:00Z", "event_type": "egress_traffic"},
        ],
        "findings": [
            {"finding_id": "FND-55-A1", "title": "Exfiltration Hypothesis", "category": "cross_source_convergence"}
        ],
        "agent_logs": [],
    }


def test_missing_evidence_agent_identifies_all_core_gap_types(gap_analysis_test_state):
    """
    Missing Evidence Agent must identify:
    1. Incomplete correlations (cloud/destination logs)
    2. Timeline gaps (45 minutes between events 1 and 2)
    3. Missing context (absence of Windows Security.evtx & unverified hashes)
    4. Unsupported hypotheses (lacks PCAP / NetFlow for exfiltration confirmation)
    """
    result = missing_evidence_agent(gap_analysis_test_state)
    recs = result["recommendations"]

    assert len(recs) >= 4

    gap_types = {r["gap_type"] for r in recs}
    assert "incomplete_correlation" in gap_types
    assert "timeline_gap" in gap_types
    assert "missing_context" in gap_types
    assert "unsupported_hypothesis" in gap_types


def test_recommendation_structure_and_disclaimer(gap_analysis_test_state):
    """
    Every recommendation must contain:
    recommendation, reason, related_finding_id, related_evidence_ids, priority, disclaimer.
    Must NOT present recommendations as mandatory conclusions.
    """
    result = missing_evidence_agent(gap_analysis_test_state)
    recs = result["recommendations"]

    for r in recs:
        assert "recommendation" in r
        assert len(r["recommendation"]) > 5
        assert "reason" in r
        assert len(r["reason"]) > 10
        assert "priority" in r
        assert r["priority"] in ["critical", "high", "medium", "low"]
        assert "related_evidence_ids" in r
        assert isinstance(r["related_evidence_ids"], list)
        assert "disclaimer" in r
        assert "not as a mandatory conclusion" in r["disclaimer"]
        assert "Advisory" in r["disclaimer"]


def test_recommendation_priority_enum():
    """Verify recommendation priority enum values."""
    assert RecommendationPriority.CRITICAL.value == "critical"
    assert RecommendationPriority.HIGH.value == "high"
    assert RecommendationPriority.MEDIUM.value == "medium"
    assert RecommendationPriority.LOW.value == "low"
