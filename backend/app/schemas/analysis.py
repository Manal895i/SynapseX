import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.agents.state import (
    CorrelationItem,
    ExtractedEntity,
    GraphState,
    InvestigationFinding,
    InvestigationRecommendation,
    TimelineEntry,
)
from app.models.analysis import AnalysisStatus


class AnalysisStartRequest(BaseModel):
    """Optional configuration parameters when triggering multi-agent analysis."""
    focus_evidence_ids: Optional[List[int]] = Field(
        default=None, description="Optional subset of evidence IDs to focus analysis on."
    )
    notes: Optional[str] = Field(default=None, description="Investigator focus notes or instructions.")


class AnalysisStartResponse(BaseModel):
    """Immediate response confirming the initiation of an analysis job."""
    analysis_id: int
    case_id: int
    status: AnalysisStatus
    message: str
    created_at: datetime.datetime


class AnalysisJobResponse(BaseModel):
    """Detailed view of an AI Multi-Agent analysis execution."""
    id: int
    case_id: int
    requested_by: Optional[int] = None
    requester_name: Optional[str] = None
    status: AnalysisStatus
    summary: Optional[str] = None
    error_message: Optional[str] = None

    # Granular analysis outputs parsed from state_snapshot
    findings: List[InvestigationFinding] = Field(default_factory=list)
    recommendations: List[InvestigationRecommendation] = Field(default_factory=list)
    extracted_entities: List[ExtractedEntity] = Field(default_factory=list)
    correlations: List[CorrelationItem] = Field(default_factory=list)
    timeline: List[TimelineEntry] = Field(default_factory=list)
    graph: Optional[GraphState] = None
    report_summary: Optional[Dict[str, Any]] = None
    agent_logs: List[Dict[str, Any]] = Field(default_factory=list)

    created_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisJobListResponse(BaseModel):
    """List of all analysis jobs run for a specific case."""
    case_id: int
    total: int
    items: List[AnalysisJobResponse]
