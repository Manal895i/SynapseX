"""
Timeline Routes for ADEIP.
Provides endpoints for chronologically sequenced, clustered investigation events.
"""
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.timeline import CaseTimelineResponse
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/cases", tags=["Case Timeline"])


@router.get(
    "/{case_id}/timeline",
    response_model=CaseTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chronologically reconstructed timeline with time clustering and sequence detection",
)
def get_case_timeline(
    case_id: int,
    start_time: Optional[datetime.datetime] = Query(None, description="Filter events occurring on or after this timestamp (ISO format)"),
    end_time: Optional[datetime.datetime] = Query(None, description="Filter events occurring on or before this timestamp (ISO format)"),
    evidence_id: Optional[int] = Query(None, description="Filter events originating from a specific evidence artifact ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type (e.g. structured_row, json_record, log_entry, windows_event)"),
    window_minutes: int = Query(5, ge=1, le=1440, description="Time window size (in minutes) for grouping events into temporal clusters"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Observed events per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Reconstructs the forensic timeline for an investigation case:
    1. Normalizes all timestamps to UTC while preserving original timestamps.
    2. Sequentially sorts events from multiple evidence sources.
    3. Groups events into temporal clusters based on `window_minutes`.
    4. Identifies notable deterministic sequences with explicit non-causation disclaimers.

    Distinguishes strictly between observed events and possible temporal relationships.
    """
    return TimelineService.get_case_timeline(
        db=db,
        case_id=case_id,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
        evidence_id=evidence_id,
        event_type=event_type,
        window_minutes=window_minutes,
        page=page,
        page_size=page_size,
    )
