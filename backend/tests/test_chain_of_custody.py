import pytest
from app.models.custody import CustodyAction


def test_custody_action_enum_values():
    """All required forensic lifecycle actions must be defined."""
    expected = {
        "evidence_uploaded",
        "integrity_verified",
        "evidence_viewed",
        "processing_started",
        "processing_completed",
        "analysis_requested",
        "report_generated",
    }
    actual = {action.value for action in CustodyAction}
    assert expected == actual


def test_custody_action_upload_is_first_event():
    """EVIDENCE_UPLOADED should be the expected initial action on ingest."""
    assert CustodyAction.EVIDENCE_UPLOADED.value == "evidence_uploaded"


def test_custody_action_integrity_verified():
    """Verify integrity check action is properly named."""
    assert CustodyAction.INTEGRITY_VERIFIED.value == "integrity_verified"


def test_custody_action_analysis_requested():
    """Verify future analysis hook action is available."""
    assert CustodyAction.ANALYSIS_REQUESTED.value == "analysis_requested"


def test_custody_action_report_generated():
    """Verify report generation action is available for future agent integration."""
    assert CustodyAction.REPORT_GENERATED.value == "report_generated"
