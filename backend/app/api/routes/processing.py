import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.investigation_event import InvestigationEvent
from app.models.user import User
from app.schemas.processing import (
    InvestigationEventListResponse,
    InvestigationEventResponse,
)

router = APIRouter(prefix="/evidence", tags=["Evidence Processing"])


@router.get(
    "/{evidence_id}/events",
    response_model=InvestigationEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List normalized investigation events extracted from an evidence artifact",
)
def list_evidence_events(
    evidence_id: int,
    event_type: Optional[str] = Query(None, description="Filter by event_type (e.g. structured_row, log_entry)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns normalized investigation events extracted from the evidence artifact,
    ordered by their source timestamp (earliest first), then by insertion order.
    """
    stmt = select(InvestigationEvent).where(InvestigationEvent.evidence_id == evidence_id)
    if event_type:
        stmt = stmt.where(InvestigationEvent.event_type == event_type.strip())

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = stmt.order_by(
        InvestigationEvent.timestamp.asc().nullslast(),
        InvestigationEvent.id.asc(),
    ).offset((page - 1) * page_size).limit(page_size)

    items = list(db.scalars(stmt).all())

    return InvestigationEventListResponse(
        evidence_id=evidence_id,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[InvestigationEventResponse.model_validate(e) for e in items],
    )
