import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.api.dependencies.rbac import require_roles
from app.models.user import User, UserRole
from app.schemas.audit import AuditEventResponse, AuditLogListResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

# Only admin and supervisor can access audit logs
_audit_reader = require_roles(UserRole.ADMIN, UserRole.SUPERVISOR, allow_admin_override=False)


@router.get(
    "",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List system-wide audit events (admin/supervisor only)",
)
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action (e.g. login, case_created)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource domain (e.g. evidence, case)"),
    user_id: Optional[int] = Query(None, description="Filter events by a specific actor user ID"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Events per page (max 200)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_audit_reader),
):
    """
    Returns a paginated, filterable list of system-wide audit events.

    Access restricted to **admin** and **supervisor** roles only.
    Passwords, tokens, and API keys are never stored in audit details.
    """
    events, total = AuditService.query_logs(
        db=db,
        current_user=current_user,
        action_filter=action,
        resource_type_filter=resource_type,
        user_id_filter=user_id,
        page=page,
        page_size=page_size,
    )

    def _to_response(e) -> AuditEventResponse:
        return AuditEventResponse(
            id=e.id,
            user_id=e.user_id,
            actor_name=e.user.full_name if e.user else "System",
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            details=e.details,
            ip_address=e.ip_address,
            created_at=e.created_at,
        )

    return AuditLogListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        items=[_to_response(e) for e in events],
    )
