"""
Unit tests for ADEIP LangGraph AI Multi-Agent Intelligence Architecture.
"""
import pytest
from app.agents.chief_agent import chief_agent
from app.agents.correlation_agent import correlation_agent
from app.agents.evidence_agent import evidence_agent
from app.agents.graph import run_investigation
from app.agents.graph_agent import graph_agent
from app.agents.missing_evidence_agent import missing_evidence_agent
from app.agents.reasoning_agent import reasoning_agent
from app.agents.report_agent import report_agent
from app.agents.state import InvestigationState
from app.agents.timeline_agent import timeline_agent


@pytest.fixture
def sample_investigation_state() -> InvestigationState:
    """Fixture providing a mock investigation state populated with multi-source evidence and events."""
    return {
        "case_id": 101,
        "evidence_ids": [1, 2],
        "event_ids": [10, 11, 12],
        "case_info": {
            "id": 101,
            "case_number": "CASE-2026-00101",
            "title": "Operation Cyber Vault",
            "description": "Unauthorized data exfiltration investigation",
            "priority": "high",
            "status": "active",
        },
        "evidence_items": [
            {
                "id": 1,
                "evidence_number": "EVD-2026-AAA01",
                "original_filename": "firewall_traffic.csv",
                "mime_type": "text/csv",
                "sha256_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
                "processing_status": "completed",
                "integrity_status": "verified",
            },
            {
                "id": 2,
                "evidence_number": "EVD-2026-BBB02",
                "original_filename": "auth_events.json",
                "mime_type": "application/json",
                "sha256_hash": "f9e8d7c6b5a43210f9e8d7c6b5a43210f9e8d7c6b5a43210f9e8d7c6b5a43210",
                "processing_status": "completed",
                "integrity_status": "verified",
            },
        ],
        "raw_events": [
            {
                "id": 10,
                "evidence_id": 1,
                "event_type": "structured_row",
                "timestamp": "2026-08-20T10:00:00Z",
                "source": "firewall_traffic.csv",
                "entity_type": "ip_address",
                "entity_value": "198.51.100.45",
                "metadata": {"src_ip": "198.51.100.45", "dst_ip": "10.0.0.5", "bytes": 45000},
            },
            {
                "id": 11,
                "evidence_id": 2,
                "event_type": "json_record",
                "timestamp": "2026-08-20T10:05:00Z",
                "source": "auth_events.json",
                "entity_type": "ip_address",
                "entity_value": "198.51.100.45",
                "metadata": {"remote_ip": "198.51.100.45", "user": "admin@adeip.internal", "action": "login_failed"},
            },
            {
                "id": 12,
                "evidence_id": 1,
                "event_type": "structured_row",
                "timestamp": "2026-08-20T10:15:00Z",
                "source": "firewall_traffic.csv",
                "entity_type": "ip_address",
                "entity_value": "198.51.100.45",
                "metadata": {"src_ip": "198.51.100.45", "dst_ip": "10.0.0.5", "bytes": 980000},
            },
        ],
        "extracted_entities": [],
        "timeline": [],
        "correlations": [],
        "graph": {},
        "findings": [],
        "recommendations": [],
        "report_summary": None,
        "agent_logs": [],
        "errors": [],
        "status": "started",
    }


def test_chief_agent_initialization(sample_investigation_state):
    """Chief agent should initialize investigation scope and add agent log."""
    res = chief_agent(sample_investigation_state)
    assert res["status"] == "in_progress"
    assert len(res["agent_logs"]) >= 1
    assert res["agent_logs"][-1]["agent"] == "chief_agent"


def test_evidence_agent_extracts_entities(sample_investigation_state):
    """Evidence agent should extract file hashes, IPs, and emails with evidence IDs & event IDs."""
    res = evidence_agent(sample_investigation_state)
    entities = res["extracted_entities"]
    assert len(entities) >= 3

    # Check that file hashes were extracted
    hashes = [e for e in entities if e["entity_type"] == "file_hash"]
    assert len(hashes) == 2

    # Check that IP address 198.51.100.45 was extracted with linked evidence/events
    ips = [e for e in entities if e["entity_type"] == "ip_address" and e["entity_value"] == "198.51.100.45"]
    assert len(ips) >= 1
    assert 10 in ips[0]["event_ids"] or 11 in ips[0]["event_ids"]


def test_timeline_agent_ordering(sample_investigation_state):
    """Timeline agent should sequence events chronologically."""
    sample_investigation_state.update(evidence_agent(sample_investigation_state))
    res = timeline_agent(sample_investigation_state)
    timeline = res["timeline"]
    assert len(timeline) == 3
    # Check chronological ordering
    assert timeline[0]["timestamp"] <= timeline[1]["timestamp"] <= timeline[2]["timestamp"]
    assert timeline[0]["evidence_id"] == 1


def test_correlation_agent_cross_evidence(sample_investigation_state):
    """Correlation agent should discover cross-evidence links for shared IP."""
    sample_investigation_state.update(evidence_agent(sample_investigation_state))
    sample_investigation_state.update(timeline_agent(sample_investigation_state))
    res = correlation_agent(sample_investigation_state)
    correlations = res["correlations"]
    assert len(correlations) >= 1

    cross_ev = [c for c in correlations if c["correlation_type"] == "cross_evidence_match"]
    assert len(cross_ev) >= 1
    assert 1 in cross_ev[0]["evidence_ids"] and 2 in cross_ev[0]["evidence_ids"]


def test_graph_agent_topology(sample_investigation_state):
    """Graph agent should produce nodes and directed edges."""
    sample_investigation_state.update(evidence_agent(sample_investigation_state))
    sample_investigation_state.update(correlation_agent(sample_investigation_state))
    res = graph_agent(sample_investigation_state)
    graph = res["graph"]
    assert "nodes" in graph and "edges" in graph
    assert len(graph["nodes"]) >= 3  # Case + 2 Evidence + Entities
    assert len(graph["edges"]) >= 2  # CONTAINS_EVIDENCE edges


def test_reasoning_agent_evidence_backed(sample_investigation_state):
    """Reasoning agent should formulate findings referencing evidence IDs and event IDs."""
    sample_investigation_state.update(evidence_agent(sample_investigation_state))
    sample_investigation_state.update(correlation_agent(sample_investigation_state))
    res = reasoning_agent(sample_investigation_state)
    findings = res["findings"]
    assert len(findings) >= 1
    for f in findings:
        assert f["finding_id"].startswith("FND-101-")
        assert len(f["referenced_evidence_ids"]) > 0
        assert "confidence" in f


def test_missing_evidence_agent_recommendations(sample_investigation_state):
    """Missing evidence agent should identify gap in host EVTX logs."""
    sample_investigation_state.update(evidence_agent(sample_investigation_state))
    res = missing_evidence_agent(sample_investigation_state)
    recs = res["recommendations"]
    assert len(recs) >= 1
    assert any("Security" in r["title"] or "Authentication" in r["title"] for r in recs)


def test_report_agent_compilation(sample_investigation_state):
    """Report agent should compile metrics and executive summary."""
    sample_investigation_state.update(evidence_agent(sample_investigation_state))
    sample_investigation_state.update(timeline_agent(sample_investigation_state))
    sample_investigation_state.update(correlation_agent(sample_investigation_state))
    sample_investigation_state.update(reasoning_agent(sample_investigation_state))
    sample_investigation_state.update(missing_evidence_agent(sample_investigation_state))

    res = report_agent(sample_investigation_state)
    assert res["status"] == "completed"
    assert res["report_summary"] is not None
    assert res["report_summary"]["case_id"] == 101
    assert "executive_summary" in res["report_summary"]


def test_end_to_end_investigation_graph_pipeline(sample_investigation_state):
    """End-to-end investigation graph execution through run_investigation()."""
    final_state = run_investigation(sample_investigation_state)

    assert final_state["status"] == "completed"
    assert len(final_state["extracted_entities"]) > 0
    assert len(final_state["timeline"]) == 3
    assert len(final_state["correlations"]) > 0
    assert len(final_state["findings"]) > 0
    assert len(final_state["recommendations"]) > 0
    assert final_state["graph"]["nodes"] is not None
    assert final_state["report_summary"] is not None
    assert len(final_state["agent_logs"]) == 8  # all 8 agents executed
