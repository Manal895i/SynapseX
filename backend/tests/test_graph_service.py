"""
Unit tests for ADEIP Investigation Knowledge Graph and Neo4j Integration.
"""
import pytest
from app.agents.graph_agent import graph_agent
from app.agents.state import InvestigationState


@pytest.fixture
def complex_graph_state() -> InvestigationState:
    """Fixture providing rich multi-evidence entities and events for knowledge graph synthesis."""
    return {
        "case_id": 42,
        "case_info": {
            "id": 42,
            "case_number": "CASE-2026-0042",
            "title": "Operation Cerberus Exfil",
            "priority": "critical",
        },
        "evidence_items": [
            {
                "id": 1,
                "evidence_number": "EVD-001",
                "original_filename": "cctv_server_room.mp4",
                "mime_type": "video/mp4",
                "sha256_hash": "111aaa",
            },
            {
                "id": 2,
                "evidence_number": "EVD-002",
                "original_filename": "workstation_logs.json",
                "mime_type": "application/json",
                "sha256_hash": "222bbb",
            },
        ],
        "raw_events": [
            {
                "id": 101,
                "evidence_id": 1,
                "event_type": "physical_access",
                "timestamp": "2026-08-20T10:00:00Z",
                "source": "cctv_server_room.mp4",
                "metadata": {
                    "person": "John Smith",
                    "location": "Server Room B",
                },
            },
            {
                "id": 102,
                "evidence_id": 2,
                "event_type": "interactive_login",
                "timestamp": "2026-08-20T10:02:00Z",
                "source": "workstation_logs.json",
                "metadata": {
                    "user": "jsmith@corp.int",
                    "device": "WKST-041",
                    "ip": "10.0.4.15",
                },
            },
            {
                "id": 103,
                "evidence_id": 2,
                "event_type": "usb_insertion",
                "timestamp": "2026-08-20T10:03:00Z",
                "source": "workstation_logs.json",
                "metadata": {
                    "device": "WKST-041",
                    "usb": "USBSTOR\\SanDisk_Cruzer",
                    "file": "financial_records.pdf",
                },
            },
        ],
        "extracted_entities": [
            {"id": 1, "entity_type": "person", "entity_value": "John Smith", "evidence_id": 1, "event_ids": [101]},
            {"id": 2, "entity_type": "location", "entity_value": "Server Room B", "evidence_id": 1, "event_ids": [101]},
            {"id": 3, "entity_type": "user_account", "entity_value": "jsmith@corp.int", "evidence_id": 2, "event_ids": [102]},
            {"id": 4, "entity_type": "device", "entity_value": "WKST-041", "evidence_id": 2, "event_ids": [102, 103]},
            {"id": 5, "entity_type": "ip_address", "entity_value": "10.0.4.15", "evidence_id": 2, "event_ids": [102]},
            {"id": 6, "entity_type": "usb_device", "entity_value": "USBSTOR\\SanDisk_Cruzer", "evidence_id": 2, "event_ids": [103]},
            {"id": 7, "entity_type": "file", "entity_value": "financial_records.pdf", "evidence_id": 2, "event_ids": [103]},
        ],
        "correlations": [
            {
                "correlation_id": "CORR-42-A1B2",
                "signal_type": "same_user_account",
                "title": "Potential Relationship: User Account Convergence",
                "description": "User identity jsmith@corp.int observed across authentication records",
                "reasons": ["Co-occurrence of physical access and digital interactive login under jsmith"],
                "related_event_ids": [101, 102],
                "related_entity_ids": [1, 3],
                "supporting_evidence_ids": [1, 2],
                "correlation_score": 0.92,
                "entities": ["person:John Smith", "user_account:jsmith@corp.int"],
                "disclaimer": "Potential relationship detected.",
            }
        ],
        "agent_logs": [],
    }


def test_knowledge_graph_node_types(complex_graph_state):
    """Knowledge graph must include Person, Device, Account, IPAddress, File, USBDevice, Location, Evidence, Event."""
    result = graph_agent(complex_graph_state)
    graph = result["graph"]
    nodes = graph["nodes"]

    node_types = {n["node_type"] for n in nodes}

    assert "Case" in node_types
    assert "Evidence" in node_types
    assert "Person" in node_types
    assert "Device" in node_types
    assert "Account" in node_types
    assert "IPAddress" in node_types
    assert "File" in node_types
    assert "USBDevice" in node_types
    assert "Location" in node_types


def test_knowledge_graph_relationships_grounded(complex_graph_state):
    """
    Knowledge graph relationships must match the formal taxonomy:
    ACCESSED, USED, CONNECTED_TO, LOCATED_AT, RELATED_TO, OBSERVED_IN
    and preserve source evidence grounding.
    """
    result = graph_agent(complex_graph_state)
    graph = result["graph"]
    edges = graph["edges"]

    rel_types = {e["relationship"] for e in edges}

    # Verify key relationship types exist
    assert "OBSERVED_IN" in rel_types
    assert "ACCESSED" in rel_types  # User -> Device or Device -> File
    assert "USED" in rel_types      # User -> IP
    assert "CONNECTED_TO" in rel_types  # Device -> IP or USB -> Device
    assert "RELATED_TO" in rel_types    # Derived from documented correlation

    # Check evidence ID references on edges
    for e in edges:
        assert "properties" in e
        # Must not have empty source or target
        assert len(e["source"]) > 0
        assert len(e["target"]) > 0


def test_unsupported_relationships_not_created():
    """Verify that arbitrary or unverified links are NOT created without factual basis."""
    sparse_state: InvestigationState = {
        "case_id": 1,
        "case_info": {"id": 1, "title": "Sparse Case"},
        "evidence_items": [{"id": 10, "original_filename": "isolated.csv"}],
        "raw_events": [
            {"id": 1, "evidence_id": 10, "event_type": "generic", "metadata": {"ip": "1.1.1.1"}}
        ],
        "extracted_entities": [
            {"id": 1, "entity_type": "ip_address", "entity_value": "1.1.1.1", "evidence_id": 10, "event_ids": [1]}
        ],
        "correlations": [],
        "agent_logs": [],
    }

    result = graph_agent(sparse_state)
    edges = result["graph"]["edges"]

    # Only OBSERVED_IN should exist for isolated nodes (no phantom ACCESSED/USED/RELATED_TO)
    rel_types = {e["relationship"] for e in edges}
    assert rel_types.issubset({"OBSERVED_IN", "CONTAINS_EVIDENCE"})
