"""
Investigation Report Routes for ADEIP.
Provides endpoints for generating, listing, and viewing structured forensic investigation reports.
"""
from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.user import User
from app.schemas.report import (
    ReportDetailResponse,
    ReportGenerateRequest,
    ReportListResponse,
    ReportResponse,
)
from app.services.report_service import ReportService

# Router 1: Case-scoped report generation & list
case_report_router = APIRouter(prefix="/cases", tags=["Case Investigation Reports"])

# Router 2: Direct report viewing & HTML export
report_router = APIRouter(prefix="/reports", tags=["Investigation Reports"])


@case_report_router.post(
    "/{case_id}/reports/generate",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a comprehensive 12-section investigation report (JSON & HTML)",
)
def generate_case_report(
    case_id: int,
    req: ReportGenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates a formal 12-section digital forensic investigation report:
    1. Case Summary
    2. Evidence Inventory
    3. Evidence Integrity Status
    4. Investigation Timeline
    5. Entity Relationships
    6. Correlations
    7. AI-Assisted Findings
    8. Supporting Evidence Mapping
    9. Alternative Explanations
    10. Recommended Verification
    11. Investigator Review Status
    12. Limitations & Uncertainty Declarations

    **Mandatory Disclaimer**: "AI-Assisted Draft — Requires Human Investigator Review"
    """
    client_ip = request.client.host if request.client else None
    return ReportService.generate_case_report(
        db=db,
        case_id=case_id,
        req=req,
        current_user=current_user,
        client_ip=client_ip,
    )


@case_report_router.get(
    "/{case_id}/reports",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all generated investigation reports for a case",
)
def list_case_reports(
    case_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves a paginated list of generated reports for a case.
    """
    return ReportService.list_case_reports(
        db=db,
        case_id=case_id,
        page=page,
        page_size=page_size,
    )


@report_router.get(
    "/{report_id}",
    response_model=ReportDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full investigation report details and structured data",
)
def get_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves full report details, 12-section structured payload, and rendered HTML.
    """
    return ReportService.get_report_detail(db=db, report_id_str=report_id)


@report_router.get(
    "/{report_id}/html",
    response_class=HTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="View rendered standalone HTML investigation report in browser",
)
def view_html_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the standalone rendered HTML forensic report for direct browser viewing or printing.
    """
    report = ReportService.get_report_detail(db=db, report_id_str=report_id)
    if not report.html_content:
        # Re-render on demand
        rendered = ReportService._render_html_report(report.report_data.model_dump())
        return HTMLResponse(content=rendered)
    return HTMLResponse(content=report.html_content)
