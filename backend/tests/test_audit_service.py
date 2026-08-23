import pytest
from app.core.audit_actions import AuditAction, AuditResourceType
from app.services.audit_service import _scrub_sensitive


# --- AuditAction enum tests ---

def test_audit_actions_contain_required_events():
    """All required system events must be present in the AuditAction enum."""
    required = {
        "login", "case_created", "case_updated",
        "evidence_uploaded", "evidence_verified",
        "analysis_started", "finding_reviewed", "report_generated",
    }
    actual = {action.value for action in AuditAction}
    missing = required - actual
    assert not missing, f"Missing AuditAction values: {missing}"


def test_audit_resource_types_defined():
    """All resource domains should be available."""
    expected = {"auth", "case", "evidence", "analysis", "finding", "report", "user", "system"}
    actual = {r.value for r in AuditResourceType}
    assert expected == actual


# --- Sensitive field scrubbing tests ---

def test_scrub_removes_password():
    data = {"user_id": 1, "password": "SuperSecret123!", "action": "login"}
    result = _scrub_sensitive(data)
    assert result["password"] == "***REDACTED***"
    assert result["user_id"] == 1
    assert result["action"] == "login"


def test_scrub_removes_token():
    data = {"access_token": "eyJhbGciOiJIUzI1Ni...", "user_id": 2}
    result = _scrub_sensitive(data)
    assert result["access_token"] == "***REDACTED***"
    assert result["user_id"] == 2


def test_scrub_removes_api_key():
    data = {"api_key": "sk-abc123", "endpoint": "/api/analyze"}
    result = _scrub_sensitive(data)
    assert result["api_key"] == "***REDACTED***"
    assert result["endpoint"] == "/api/analyze"


def test_scrub_removes_multiple_sensitive_keys():
    data = {
        "password": "pass",
        "access_token": "tok",
        "api_key": "key",
        "case_id": 5,
        "evidence_number": "EVD-2026-XXXXX",
    }
    result = _scrub_sensitive(data)
    assert result["password"] == "***REDACTED***"
    assert result["access_token"] == "***REDACTED***"
    assert result["api_key"] == "***REDACTED***"
    assert result["case_id"] == 5
    assert result["evidence_number"] == "EVD-2026-XXXXX"


def test_scrub_none_returns_none():
    """None details input must return None without error."""
    assert _scrub_sensitive(None) is None


def test_scrub_empty_dict_returns_empty():
    assert _scrub_sensitive({}) == {}


def test_scrub_preserves_safe_fields():
    data = {"case_id": 10, "status": "active", "sha256_hash": "abc123"}
    result = _scrub_sensitive(data)
    assert result == data
