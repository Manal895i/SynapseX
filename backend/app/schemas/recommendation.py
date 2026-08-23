"""
Missing Evidence Agent & Recommendation Pydantic Schemas for ADEIP.
"""
import datetime
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.recommendation import RecommendationPriority


class RecommendationResponse(BaseModel):
    """
    Public representation of an actionable advisory recommendation.
    Rule: Framed as non-mandatory investigative acquisition guidance.
    """
    id: int
    recommendation_id: str
    case_id: int
    recommendation: str
    reason: str
    gap_type: str
    priority: RecommendationPriority
    related_finding_id: Optional[str] = None
    related_evidence_ids: List[int] = Field(default_factory=list)
    suggested_source: Optional[str] = None
    disclaimer: str = "Advisory recommendation. Presented as investigative acquisition guidance and not as a mandatory conclusion."
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationListResponse(BaseModel):
    """Paginated list of recommendations for an investigation case."""
    case_id: int
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[RecommendationResponse]


class RecommendationRunResultResponse(BaseModel):
    """Result returned after executing the Missing Evidence Agent on a case."""
    case_id: int
    recommendations_generated: int
    new_recommendations_saved: int
    breakdown_by_priority: Dict[str, int] = Field(default_factory=dict)
    breakdown_by_gap_type: Dict[str, int] = Field(default_factory=dict)
    items: List[RecommendationResponse] = Field(default_factory=list)
