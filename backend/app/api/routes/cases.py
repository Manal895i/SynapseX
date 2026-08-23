from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.case import CasePriority, CaseStatus
from app.models.user import User
from app.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseUpdateRequest,
)
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new investigation case",
)
async def create_case(
    case_in: CaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates a new digital forensic case.
    Automatically assigns created_by to the current authenticated investigator/admin.
    """
    return CaseService.create_case(db=db, case_in=case_in, current_user=current_user)


@router.get(
    "",
    response_model=CaseListResponse,
    status_code=status.HTTP_200_OK,
    summary="List investigation cases with search and pagination",
)
async def list_cases(
    search: Optional[str] = Query(None, description="Search keyword in case number, title, or description"),
    case_status: Optional[CaseStatus] = Query(None, alias="status", description="Filter by case lifecycle status"),
    priority: Optional[CasePriority] = Query(None, description="Filter by priority level"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves a paginated list of cases matching search criteria and filters.
    """
    items, total, total_pages = CaseService.list_cases(
        db=db,
        current_user=current_user,
        search=search,
        status_filter=case_status,
        priority_filter=priority,
        page=page,
        page_size=page_size,
    )
    return CaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Get case details by ID",
)
async def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns full details of an authorized investigation case.
    """
    return CaseService.get_case(db=db, case_id=case_id, current_user=current_user)


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Update case metadata, status, or priority",
)
async def update_case(
    case_id: int,
    case_in: CaseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Applies partial updates to a case. Restricted to case creator, assigned investigator, or supervisors/admins.
    """
    return CaseService.update_case(
        db=db,
        case_id=case_id,
        case_in=case_in,
        current_user=current_user,
    )


@router.delete(
    "/{case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an investigation case",
)
async def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Deletes an investigation case record. Restricted to Supervisors and Admins.
    """
    CaseService.delete_case(db=db, case_id=case_id, current_user=current_user)
    return None
