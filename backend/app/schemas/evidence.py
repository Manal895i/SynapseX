import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.evidence import IntegrityStatus, ProcessingStatus


class EvidenceResponse(BaseModel):
    """
    Public representation of uploaded evidence artifact.
    Omits raw internal server filesystem paths to maintain security.
    """
    id: int
    evidence_number: str
    case_id: int
    original_filename: str
    mime_type: str
    file_size: int = Field(..., description="File size in bytes")
    sha256_hash: str = Field(..., description="Cryptographic SHA-256 integrity hash")
    processing_status: ProcessingStatus
    integrity_status: IntegrityStatus
    last_verified_at: Optional[datetime.datetime] = None
    uploaded_by: int
    uploader_name: Optional[str] = None
    uploaded_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceListResponse(BaseModel):
    """Collection of evidence items associated with an investigation case."""
    items: List[EvidenceResponse]
    total: int


class EvidenceVerificationResponse(BaseModel):
    """Result of cryptographic on-disk SHA-256 integrity verification."""
    evidence_id: int
    evidence_number: str
    original_filename: str
    integrity_status: IntegrityStatus
    stored_hash: str
    computed_hash: Optional[str] = None
    is_valid: bool = Field(..., description="True if computed hash matches stored hash; False if mismatch or file missing")
    verified_at: datetime.datetime
    verified_by: int
    verifier_name: Optional[str] = None
    message: str
