"""
Investigation Report Pydantic Schemas for ADEIP.

Strictly structures the 12 required report sections and enforces the mandatory disclaimer:
"AI-Assisted Draft — Requires Human Investigator Review"
"""
import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportFormat

_MANDATORY_DISCLAIMER = "AI-Assisted Draft — Requires Human Investigator Review"


class ReportGenerateRequest(BaseModel):
    """Request options for generating a structured investigation report."""
    title: Optional[str] = Field(default=None, description="Custom title for the investigation report.")
    report_format: ReportFormat = Field(default=ReportFormat.HTML, description="Output format: 'json', 'html', or 'markdown'.")


class StructuredReportData(BaseModel):
    """
    Standardized 12-section forensic report data model.
    Every finding preserves references to source evidence IDs and event IDs.
    """
    disclaimer: str = Field(default=_MANDATORY_DISCLAIMER)
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Section 1: Case Summary
    case_summary: Dict[str, Any] = Field(default_factory=dict)

    # Section 2: Evidence Inventory
    evidence_inventory: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 3: Evidence Integrity Status
    evidence_integrity_status: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 4: Investigation Timeline
    investigation_timeline: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 5: Entity Relationships
    entity_relationships: Dict[str, Any] = Field(default_factory=dict)

    # Section 6: Correlations
    correlations: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 7: AI-Assisted Findings
    ai_assisted_findings: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 8: Supporting Evidence (Mapped per finding)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 9: Alternative Explanations
    alternative_explanations: List[str] = Field(default_factory=list)

    # Section 10: Recommended Verification
    recommended_verification: List[str] = Field(default_factory=list)

    # Section 11: Investigator Review Status
    investigator_review_status: List[Dict[str, Any]] = Field(default_factory=list)

    # Section 12: Limitations
    limitations: List[str] = Field(default_factory=list)


class ReportResponse(BaseModel):
    """Public summary representation of an investigation report."""
    id: int
    report_id: str
    case_id: int
    title: str
    report_format: ReportFormat
    disclaimer: str = _MANDATORY_DISCLAIMER
    generated_by: Optional[int] = None
    author_name: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ReportDetailResponse(ReportResponse):
    """Detailed representation containing the complete 12-section structured payload and HTML preview."""
    report_data: StructuredReportData
    html_content: Optional[str] = None


class ReportListResponse(BaseModel):
    """Paginated list of investigation reports for a case."""
    case_id: int
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ReportResponse]
