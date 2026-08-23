from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.custody import ChainOfCustodyResponse
from app.schemas.evidence import (
    EvidenceListResponse,
    EvidenceResponse,
    EvidenceVerificationResponse,
)
from app.services.custody_service import CustodyService
from app.services.evidence_service import EvidenceService

# Router 1: Case-scoped evidence routes (/api/cases/{case_id}/evidence)
case_evidence_router = APIRouter(prefix="/cases", tags=["Case Evidence"])

# Router 2: Direct evidence item routes (/api/evidence/{evidence_id})
evidence_router = APIRouter(prefix="/evidence", tags=["Evidence Intelligence"])


@case_evidence_router.post(
    "/{case_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Securely upload a forensic evidence artifact",
)
async def upload_case_evidence(
    case_id: int,
    request: Request,
    file: UploadFile = File(..., description="Forensic evidence file (CSV, JSON, TXT, PDF, JPG, PNG, MP4, EVTX)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Streams and cryptographically validates (SHA-256) an evidence file into isolated secure storage.
    Enforces file type allowlist, size boundaries, path traversal immunity, and audit logging.
    Automatically creates the first chain-of-custody event: evidence_uploaded.
    """
    client_ip = request.client.host if request.client else None
    return await EvidenceService.upload_evidence(
        db=db,
        case_id=case_id,
        file=file,
        current_user=current_user,
        client_ip=client_ip,
    )


@case_evidence_router.get(
    "/{case_id}/evidence",
    response_model=EvidenceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all evidence items registered to a case",
)
async def list_case_evidence(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves safe forensic metadata for all evidence artifacts attached to the specified case.
    """
    items = EvidenceService.list_evidence_for_case(db=db, case_id=case_id, current_user=current_user)
    return EvidenceListResponse(items=items, total=len(items))


@evidence_router.get(
    "/{evidence_id}",
    response_model=EvidenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single evidence artifact metadata",
)
async def get_evidence_detail(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves safe metadata and processing status for an individual evidence artifact.
    """
    return EvidenceService.get_evidence(db=db, evidence_id=evidence_id, current_user=current_user)


@evidence_router.post(
    "/{evidence_id}/verify",
    response_model=EvidenceVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify cryptographic evidence integrity (SHA-256)",
)
async def verify_evidence_integrity(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Reads the stored evidence file in read-only mode, recalculates its SHA-256 hash,
    compares it with the original hash, records an audit event, and appends an
    integrity_verified chain-of-custody entry.
    """
    client_ip = request.client.host if request.client else None
    return EvidenceService.verify_evidence_integrity(
        db=db,
        evidence_id=evidence_id,
        current_user=current_user,
        client_ip=client_ip,
    )


@evidence_router.get(
    "/{evidence_id}/chain-of-custody",
    response_model=ChainOfCustodyResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve the complete chain-of-custody log for an evidence artifact",
)
async def get_chain_of_custody(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns all immutable chain-of-custody events for a forensic evidence artifact,
    ordered chronologically from earliest to most recent.
    Records are append-only and cannot be edited or deleted by any standard user.
    """
    return CustodyService.get_chain_for_evidence(
        db=db,
        evidence_id=evidence_id,
        current_user=current_user,
    )


@evidence_router.delete(
    "/{evidence_id}",
    status_code=status.HTTP_200_OK,
    summary="Permanently delete an evidence artifact",
)
async def delete_evidence(
    evidence_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Permanently deletes an evidence artifact, removes its file from secure disk storage,
    cascades dependent records, and logs an immutable audit trail event.
    """
    client_ip = request.client.host if request.client else None
    return EvidenceService.delete_evidence(
        db=db,
        evidence_id=evidence_id,
        current_user=current_user,
        client_ip=client_ip,
    )

