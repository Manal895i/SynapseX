import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.entity import EntityType


class EntityResponse(BaseModel):
    """
    Public structured representation of a single extracted entity.
    """
    id: int
    case_id: int
    evidence_id: int
    event_id: Optional[int] = None
    entity_type: EntityType
    entity_value: str
    normalized_value: str
    extraction_method: str
    confidence: float
    context: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EntityListResponse(BaseModel):
    """Paginated list of extracted entities."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[EntityResponse]


class EntityExtractionResultResponse(BaseModel):
    """Summary returned when triggering deterministic entity extraction on an evidence artifact."""
    evidence_id: int
    case_id: int
    total_events_scanned: int
    entities_extracted: int
    new_entities_persisted: int
    breakdown_by_type: Dict[str, int] = Field(default_factory=dict)
    sample_entities: List[EntityResponse] = Field(default_factory=list)
