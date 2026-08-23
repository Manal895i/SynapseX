import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class ProcessingResultResponse(BaseModel):
    """Response returned immediately after synchronous evidence processing."""
    evidence_id: int
    evidence_number: str
    original_filename: str
    processing_status: str
    parser_used: str
    events_extracted: int
    error: Optional[str] = None


class InvestigationEventResponse(BaseModel):
    """Safe read-only representation of a normalized investigation event."""
    id: int
    case_id: int
    evidence_id: int
    event_type: str
    timestamp: Optional[datetime.datetime] = None
    source: Optional[str] = None
    entity_type: Optional[str] = None
    entity_value: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationEventListResponse(BaseModel):
    """Paginated list of investigation events."""
    evidence_id: int
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[InvestigationEventResponse]
