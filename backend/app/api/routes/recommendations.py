"""
Missing Evidence & Recommendation Routes for ADEIP.
Provides endpoints for running gap analysis across cases and querying advisory recommendations.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationRunResultResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/cases", tags=["Case Evidence Gaps & Recommendations"])


@router.post(
    "/{case_id}/recommendations/run",
    response_model=RecommendationRunResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute the Missing Evidence Agent to identify investigation gaps and recommendations",
)
def run_case_recommendations(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes the Missing Evidence Agent for the specified case:
    1. Evaluates:
       - **Timeline Gaps**: Unmonitored intervals between observed events.
       - **Incomplete Correlations**: One-sided network transfers or unmonitored USB connections.
       - **Missing Context**: Absence of Windows Security Event Logs (Security.evtx) or unverified files.
       - **Unsupported Hypotheses**: Leads lacking packet capture (PCAP) or flow counters.
    2. Formulates structured advisory recommendations with explicit rationale and priority.
    3. Persists recommendations into the database.

    **CRITICAL RULE: Recommendations are advisory acquisition guidance and NOT mandatory conclusions.**
    """
    client_ip = request.client.host if request.client else None
    return RecommendationService.run_case_recommendations(
        db=db,
        case_id=case_id,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.get(
    "/{case_id}/recommendations",
    response_model=RecommendationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List advisory evidence gap recommendations for a case",
)
def list_case_recommendations(
    case_id: int,
    priority: Optional[str] = Query(None, description="Filter by priority (critical, high, medium, low)"),
    gap_type: Optional[str] = Query(None, description="Filter by gap type (timeline_gap, incomplete_correlation, missing_context, unsupported_hypothesis)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves stored evidence gap recommendations for a case, with support
    for filtering by priority, gap type, and pagination.
    """
    return RecommendationService.list_case_recommendations(
        db=db,
        case_id=case_id,
        priority=priority,
        gap_type=gap_type,
        page=page,
        page_size=page_size,
    )
