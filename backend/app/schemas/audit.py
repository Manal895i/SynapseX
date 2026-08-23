import datetime
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    """
    Public read-only representation of a single audit event.
    Sensitive fields are scrubbed at write time before they ever reach the DB.
    """
    id: int
    user_id: Optional[int] = None
    actor_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Paginated audit event listing response."""
    page: int
    page_size: int
    total: int
    total_pages: int
    items: List[AuditEventResponse]
