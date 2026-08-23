"""
Unit tests for ADEIP Evidence Agent (Deterministic Entity Recognition & Normalization).
"""
import pytest
from app.agents.evidence_agent import evidence_agent
from app.agents.state import InvestigationState
from app.models.entity import EntityType, ExtractionMethod
from app.services.entity_service import (
    EMAIL_PATTERN,
    IPV4_PATTERN,
    SHA256_PATTERN,
    USB_HARDWARE_PATTERN,
    _normalize_value,
)


def test_entity_type_enum_completeness():
    """Verify all requested core forensic entity types are present."""
    required = {
        "person",
        "device",
        "user_account",
        "ip_address",
        "file",
        "usb_device",
        "location",
    }
    actual = {e.value for e in EntityType}
    assert required.issubset(actual)


def test_value_normalization():
    """Verify entity normalization rules (lowercase IPs/emails/hashes, standardized slashes)."""
    assert _normalize_value(EntityType.IP_ADDRESS, " 192.168.1.50 ") == "192.168.1.50"
    assert _normalize_value(EntityType.USER_ACCOUNT, " Admin@ADEIP.Internal ") == "admin@adeip.internal"
    assert _normalize_value(EntityType.FILE, " C:\\Logs\\Security.evtx ") == "c:/logs/security.evtx"
    assert _normalize_value(EntityType.DEVICE, " workstation-alpha ") == "WORKSTATION-ALPHA"
    assert _normalize_value(EntityType.PERSON, "  Detective Connor  ") == "Detective Connor"


def test_ipv4_regex_pattern():
    """Test IPv4 pattern extraction."""
    text = "Inbound connection from 198.51.100.45:443 to internal gateway 10.0.0.1"
    matches = IPV4_PATTERN.findall(text)
    assert "198.51.100.45" in matches
    assert "10.0.0.1" in matches


def test_email_regex_pattern():
    """Test email pattern extraction."""
    text = "User john.doe@cybersec.org logged in from workstation"
    matches = EMAIL_PATTERN.findall(text)
    assert matches == ["john.doe@cybersec.org"]


def test_usb_hardware_pattern():
    """Test USB hardware pattern matching."""
    text = "Attached device USBSTOR\\Disk&Ven_SanDisk&Prod_Ultra&Rev_1.00\\AA010101 and VID_0781&PID_5581"
    matches = USB_HARDWARE_PATTERN.findall(text)
    assert len(matches) >= 2


def test_sha256_pattern():
    """Test SHA-256 hash pattern matching."""
    text = "File hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 verified"
    matches = SHA256_PATTERN.findall(text)
    assert matches == ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"]


def test_evidence_agent_extracts_all_core_entity_types():
    """
    Evidence Agent should identify person, device, user_account, ip_address,
    file, usb_device, and location from structured logs and metadata.
    """
    mock_state: InvestigationState = {
        "case_id": 1,
        "evidence_ids": [10],
        "event_ids": [100, 101, 102],
        "case_info": {"id": 1, "title": "Test Case"},
        "evidence_items": [
            {
                "id": 10,
                "original_filename": "network_perimeter_export.csv",
                "sha256_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
                "mime_type": "text/csv",
            }
        ],
        "raw_events": [
            {
                "id": 100,
                "evidence_id": 10,
                "event_type": "structured_row",
                "source": "network_perimeter_export.csv",
                "metadata": {
                    "ip": "203.0.113.195",
                    "user": "analyst.smith@adeip.internal",
                    "hostname": "HQ-DESKTOP-04",
                    "location": "Sector 7 Data Center",
                },
            },
            {
                "id": 101,
                "evidence_id": 10,
                "event_type": "structured_row",
                "source": "network_perimeter_export.csv",
                "metadata": {
                    "person": "Agent Dana Scully",
                    "usb": "USBSTOR\\Disk&Ven_Kingston&Prod_DataTraveler",
                    "file": "exfiltrated_secrets.zip",
                },
            },
        ],
        "extracted_entities": [],
        "agent_logs": [],
    }

    result = evidence_agent(mock_state)
    entities = result["extracted_entities"]

    entity_types_found = {e["entity_type"] for e in entities}

    # Verify all 7 requested entity types were extracted
    assert "person" in entity_types_found
    assert "device" in entity_types_found
    assert "user_account" in entity_types_found
    assert "ip_address" in entity_types_found
    assert "file" in entity_types_found
    assert "usb_device" in entity_types_found
    assert "location" in entity_types_found

    # Verify structured fields
    for ent in entities:
        assert "entity_type" in ent
        assert "entity_value" in ent
        assert "normalized_value" in ent
        assert "evidence_id" in ent
        assert "extraction_method" in ent
        assert ent["confidence"] > 0.8
