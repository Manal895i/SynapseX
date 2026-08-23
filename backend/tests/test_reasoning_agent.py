"""
Unit tests for ADEIP Reasoning Agent and Investigation Finding Lifecycle.
"""
import pytest
from app.agents.reasoning_agent import reasoning_agent
from app.agents.state import InvestigationState
from app.models.finding import FindingReviewStatus


@pytest.fixture
def reasoning_test_state() -> InvestigationState:
    """Fixture providing multi-source investigation state for reasoning tests."""
    return {
        "case_id": 77,
        "case_info": {"id": 77, "title": "Suspected Credential Misuse"},
        "evidence_items": [
            {"id": 1, "original_filename": "vpn_access.csv", "sha256_hash": "111aaa", "integrity_status": "verified"},
            {"id": 2, "original_filename": "host_events.json", "sha256_hash": "222bbb", "integrity_status": "unverified"},
        ],
        "raw_events": [
            {"id": 10, "evidence_id": 1, "event_type": "vpn_login", "timestamp": "2026-08-20T10:00:00Z", "metadata": {"user": "emp_042", "ip": "198.51.100.22"}},
            {"id": 11, "evidence_id": 2, "event_type": "file_read", "timestamp": "2026-08-20T10:05:00Z", "metadata": {"user": "emp_042", "file": "q2_salary.xlsx"}},
        ],
        "extracted_entities": [
            {"id": 1, "entity_type": "user_account", "entity_value": "emp_042", "evidence_id": 1, "event_ids": [10, 11]},
            {"id": 2, "entity_type": "ip_address", "entity_value": "198.51.100.22", "evidence_id": 1, "event_ids": [10]},
            {"id": 3, "entity_type": "file", "entity_value": "q2_salary.xlsx", "evidence_id": 2, "event_ids": [11]},
        ],
        "correlations": [
            {
                "correlation_id": "CORR-77-99AA",
                "signal_type": "same_user_account",
                "title": "Potential Relationship: Shared User Identity 'emp_042'",
                "description": "User emp_042 active across VPN and Host events",
                "reasons": ["Common user identity observed in VPN session and local file access"],
                "supporting_evidence_ids": [1, 2],
                "related_event_ids": [10, 11],
                "correlation_score": 0.90,
            }
        ],
        "timeline": [
            {"event_id": 10, "timestamp_utc": "2026-08-20T10:00:00Z", "event_type": "vpn_login"},
            {"event_id": 11, "timestamp_utc": "2026-08-20T10:05:00Z", "event_type": "file_read"},
        ],
        "agent_logs": [],
    }


def test_reasoning_output_contains_all_seven_required_sections(reasoning_test_state):
    """
    STEP 18 strict output requirement:
    Must contain summary, observations, potential_hypotheses, supporting_evidence,
    alternative_explanations, recommended_verification, and limitations.
    """
    result = reasoning_agent(reasoning_test_state)
    output = result["reasoning_output"]

    assert "summary" in output
    assert "observations" in output
    assert "potential_hypotheses" in output
    assert "supporting_evidence" in output
    assert "alternative_explanations" in output
    assert "recommended_verification" in output
    assert "limitations" in output

    assert len(output["observations"]) >= 1
    assert len(output["potential_hypotheses"]) >= 1
    assert len(output["alternative_explanations"]) >= 1
    assert len(output["recommended_verification"]) >= 1
    assert len(output["limitations"]) >= 1


def test_no_guilt_declaration_and_non_proof_compliance(reasoning_test_state):
    """
    Rule 1 & 2: Do not declare a person guilty. Do not treat probability as proof.
    """
    result = reasoning_agent(reasoning_test_state)
    output = result["reasoning_output"]

    full_text = " ".join([
        output["summary"],
        " ".join([str(o) for o in output["observations"]]),
        " ".join(output["potential_hypotheses"]),
        " ".join(output["alternative_explanations"]),
    ]).lower()

    # Must NOT contain definitive guilt declarations
    assert "is guilty" not in full_text
    assert "guilty of" not in full_text
    assert "perpetrator confirmed" not in full_text

    # Must state non-proof limitations
    limitations_text = " ".join(output["limitations"]).lower()
    assert "proof" in limitations_text or "not constitute" in limitations_text or "probabilistic" in limitations_text


def test_observations_reference_evidence_and_events(reasoning_test_state):
    """
    Rule 3: Every observation must reference supporting evidence or events.
    """
    result = reasoning_agent(reasoning_test_state)
    observations = result["reasoning_output"]["observations"]

    for obs in observations:
        assert "referenced_evidence_ids" in obs
        assert "referenced_event_ids" in obs
        # Must reference at least one evidence ID or event ID
        assert len(obs["referenced_evidence_ids"]) > 0 or len(obs["referenced_event_ids"]) > 0


def test_alternative_explanations_and_uncertainty(reasoning_test_state):
    """
    Rule 4 & 5: Include alternative explanations and identify uncertainty/gaps.
    """
    result = reasoning_agent(reasoning_test_state)
    output = result["reasoning_output"]

    alternatives = output["alternative_explanations"]
    assert any("compromise" in a.lower() or "sharing" in a.lower() or "automated" in a.lower() for a in alternatives)

    limitations = output["limitations"]
    # Evidence 2 is unverified in fixture -> limitations should note integrity
    assert any("integrity" in l.lower() or "unverified" in l.lower() or "sample" in l.lower() for l in limitations)


def test_finding_review_statuses():
    """Verify supported human-in-the-loop review actions."""
    assert FindingReviewStatus.ACCEPTED_AS_LEAD.value == "accepted_as_lead"
    assert FindingReviewStatus.REJECTED.value == "rejected"
    assert FindingReviewStatus.NEEDS_MORE_ANALYSIS.value == "needs_more_analysis"
    assert FindingReviewStatus.PENDING_REVIEW.value == "pending_review"
