"""
Reasoning & Findings Routes for ADEIP.
Provides endpoints for running AI reasoning over structured investigation data,
listing findings, and recording human-in-the-loop review actions.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.finding import (
    FindingListResponse,
    FindingResponse,
    FindingReviewRequest,
    ReasoningRunResultResponse,
)
from app.services.finding_service import FindingService

# Router 1: Case-scoped reasoning and findings (/api/cases/{case_id}/...)
case_finding_router = APIRouter(prefix="/cases", tags=["Case AI Reasoning & Findings"])

# Router 2: Direct finding review actions (/api/findings/{finding_id}/...)
finding_router = APIRouter(prefix="/findings", tags=["Finding Review & Governance"])


@case_finding_router.post(
    "/{case_id}/reasoning/run",
    response_model=ReasoningRunResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute the Reasoning Agent over structured case data to generate grounded findings",
)
def run_case_reasoning(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes the Reasoning Agent over structured investigation data (timeline, correlations, entities, evidence):
    - Generates 7-element structured reasoning output:
      1. Summary
      2. Grounded Observations
      3. Potential Hypotheses (Investigative Leads)
      4. Supporting Evidence References
      5. Alternative Non-Malicious Explanations
      6. Recommended Investigator Verification Steps
      7. Limitations & Uncertainty Statements
    - Persists findings in the `investigation_findings` table.
    - **Rule: AI never declares guilt; confidence is not legal proof.**
    """
    client_ip = request.client.host if request.client else None
    return FindingService.run_case_reasoning(
        db=db,
        case_id=case_id,
        current_user=current_user,
        client_ip=client_ip,
    )


@case_finding_router.get(
    "/{case_id}/findings",
    response_model=FindingListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all AI findings and investigative leads for a case",
)
def list_case_findings(
    case_id: int,
    review_status: Optional[str] = Query(None, description="Filter by review status (pending_review, accepted_as_lead, rejected, needs_more_analysis)"),
    category: Optional[str] = Query(None, description="Filter by finding category"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves stored investigation findings for a case with filtering by review status and pagination.
    """
    return FindingService.list_case_findings(
        db=db,
        case_id=case_id,
        review_status=review_status,
        category=category,
        page=page,
        page_size=page_size,
    )


@finding_router.patch(
    "/{finding_id}/review",
    response_model=FindingResponse,
    status_code=status.HTTP_200_OK,
    summary="Record investigator review action on an AI finding (Human-in-the-Loop)",
)
def review_finding(
    finding_id: str,
    review_in: FindingReviewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Records human investigator governance decision on an AI-generated finding:
    - **Review Actions**: `accepted_as_lead`, `rejected`, `needs_more_analysis`
    - Stores reviewer identity, notes, and timestamp.
    - Emits an immutable audit log record.
    - **The final decision remains with the investigator.**
    """
    client_ip = request.client.host if request.client else None
    return FindingService.review_finding(
        db=db,
        finding_id_str=finding_id,
        review_in=review_in,
        current_user=current_user,
        client_ip=client_ip,
    )
