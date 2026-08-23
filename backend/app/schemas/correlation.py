import datetime
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CorrelationResponse(BaseModel):
    """
    Public representation of an explainable correlation signal.
    Rule: Emphasizes non-proof wording ("Potential relationship detected").
    """
    id: int
    case_id: int
    correlation_id: str
    signal_type: str
    title: str
    description: str
    correlation_score: float = Field(..., ge=0.0, le=1.0)
    related_event_ids: List[int] = Field(default_factory=list)
    related_entity_ids: List[int] = Field(default_factory=list)
    supporting_evidence_ids: List[int] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    disclaimer: str = "Potential relationship detected. Observational correlation does not establish causation or definitive proof."
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CorrelationListResponse(BaseModel):
    """Paginated list of correlations for an investigation case."""
    case_id: int
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[CorrelationResponse]


class CorrelationRunResultResponse(BaseModel):
    """Summary returned after executing the correlation agent on a case."""
    case_id: int
    correlations_identified: int
    new_correlations_saved: int
    breakdown_by_signal: Dict[str, int] = Field(default_factory=dict)
    items: List[CorrelationResponse] = Field(default_factory=list)
