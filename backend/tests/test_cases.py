import pytest
from pydantic import ValidationError
from app.models.case import CasePriority, CaseStatus
from app.schemas.case import CaseCreateRequest, CaseUpdateRequest


def test_case_create_schema_valid():
    """Verify CaseCreateRequest accepts valid inputs and sets default status/priority."""
    payload = CaseCreateRequest(
        title="Unauthorized Cyber Infiltration - Operation Alpha",
        description="Suspected exfiltration of encrypted forensic databases.",
    )
    assert payload.title == "Unauthorized Cyber Infiltration - Operation Alpha"
    assert payload.status == CaseStatus.ACTIVE
    assert payload.priority == CasePriority.MEDIUM
    assert payload.case_number is None


def test_case_create_schema_invalid_status():
    """Verify CaseCreateRequest rejects illegal status strings."""
    with pytest.raises(ValidationError):
        CaseCreateRequest(
            title="Invalid Case",
            status="non_existent_status",  # type: ignore
        )


def test_case_create_schema_invalid_priority():
    """Verify CaseCreateRequest rejects illegal priority strings."""
    with pytest.raises(ValidationError):
        CaseCreateRequest(
            title="Invalid Priority Case",
            priority="urgent_now",  # type: ignore
        )


def test_case_update_schema_partial():
    """Verify CaseUpdateRequest allows optional partial updates."""
    payload = CaseUpdateRequest(
        status=CaseStatus.UNDER_REVIEW,
        priority=CasePriority.CRITICAL,
    )
    assert payload.status == CaseStatus.UNDER_REVIEW
    assert payload.priority == CasePriority.CRITICAL
    assert payload.title is None
