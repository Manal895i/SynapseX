"""
Correlation Routes for ADEIP.
Provides endpoints for executing explainable multi-signal correlation discovery
and retrieving identified potential relationships.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.correlation import (
    CorrelationListResponse,
    CorrelationRunResultResponse,
)
from app.services.correlation_service import CorrelationService

router = APIRouter(prefix="/cases", tags=["Case Correlations"])


@router.post(
    "/{case_id}/correlations/run",
    response_model=CorrelationRunResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute explainable correlation discovery across case events and entities",
)
def run_case_correlations(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes the Correlation Agent on the specified case:
    1. Scans extracted entities and events for common indicators:
       - Same Device / USB Device
       - Same User Account / Person
       - Same IP Address
       - Same File / Cryptographic Hash
       - Shared Evidence Context
       - Timestamp Proximity
       - Multi-Signal Convergence
    2. Formulates explainable reasons for every correlation with an evidence-grounded score.
    3. Persists results into the database.

    CRITICAL RULE: Correlations are non-proof observational signals ("Potential relationship detected").
    """
    client_ip = request.client.host if request.client else None
    return CorrelationService.run_case_correlations(
        db=db,
        case_id=case_id,
        current_user=current_user,
        client_ip=client_ip,
    )


@router.get(
    "/{case_id}/correlations",
    response_model=CorrelationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List identified correlations for a case",
)
def get_case_correlations(
    case_id: int,
    signal_type: Optional[str] = Query(None, description="Filter by signal type (e.g. same_ip_address, same_device, timestamp_proximity)"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Filter correlations by minimum score (0.0 - 1.0)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves stored correlation signals for the case, with support for filtering
    by signal type, minimum correlation score, and pagination.
    """
    return CorrelationService.get_case_correlations(
        db=db,
        case_id=case_id,
        signal_type=signal_type,
        min_score=min_score,
        page=page,
        page_size=page_size,
    )
