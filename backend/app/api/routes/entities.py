"""
Entity Intelligence Routes for ADEIP.
Provides endpoints for deterministic entity extraction and querying.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.entity import (
    EntityExtractionResultResponse,
    EntityListResponse,
)
from app.services.entity_service import EntityService

# Router 1: Evidence-scoped entity endpoints
evidence_entity_router = APIRouter(prefix="/evidence", tags=["Evidence Entities"])

# Router 2: Case-scoped entity endpoints
case_entity_router = APIRouter(prefix="/cases", tags=["Case Entities"])


@evidence_entity_router.post(
    "/{evidence_id}/extract-entities",
    response_model=EntityExtractionResultResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger deterministic entity extraction for an evidence artifact",
)
def extract_entities_for_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Executes the Evidence Agent's deterministic extraction pipeline:
    - Scans evidence metadata (hashes, filenames)
    - Inspects investigation events and structured metadata
    - Extracts & normalizes person, device, user_account, ip_address, file, usb_device, location
    - Stores newly identified entities in the `extracted_entities` table.
    """
    return EntityService.extract_entities_from_evidence(
        db=db,
        evidence_id=evidence_id,
        flush=True,
    )


@evidence_entity_router.get(
    "/{evidence_id}/entities",
    response_model=EntityListResponse,
    status_code=status.HTTP_200_OK,
    summary="List normalized entities extracted from a specific evidence artifact",
)
def list_evidence_entities(
    evidence_id: int,
    entity_type: Optional[str] = Query(None, description="Filter by entity_type (e.g. ip_address, user_account, device)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves all normalized entities associated with a specific evidence artifact.
    """
    return EntityService.list_entities_for_evidence(
        db=db,
        evidence_id=evidence_id,
        entity_type=entity_type,
        page=page,
        page_size=page_size,
    )


@case_entity_router.get(
    "/{case_id}/entities",
    response_model=EntityListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all normalized entities across all evidence in a case",
)
def list_case_entities(
    case_id: int,
    entity_type: Optional[str] = Query(None, description="Filter by entity_type (e.g. ip_address, device, usb_device)"),
    search: Optional[str] = Query(None, description="Search normalized entity value"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves a unified, searchable list of all entities extracted across all evidence
    attached to the investigation case.
    """
    return EntityService.list_entities_for_case(
        db=db,
        case_id=case_id,
        entity_type=entity_type,
        search_query=search,
        page=page,
        page_size=page_size,
    )
