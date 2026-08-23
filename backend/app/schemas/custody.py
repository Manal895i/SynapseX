import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.custody import CustodyAction


class CustodyEventResponse(BaseModel):
    """
    Safe public representation of a single chain-of-custody record.
    Read-only — no create/update/delete schemas are exposed to API consumers.
    """
    id: int
    evidence_id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    action: CustodyAction
    details: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ChainOfCustodyResponse(BaseModel):
    """Ordered, immutable chain-of-custody log for an evidence artifact."""
    evidence_id: int
    evidence_number: str
    original_filename: str
    total_events: int
    events: List[CustodyEventResponse]
