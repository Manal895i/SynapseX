import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction, AuditResourceType
from app.models.audit import AuditEvent
from app.models.user import UserRole

logger = logging.getLogger("adeip.audit")

# Fields that must never appear in audit details — enforced by scrubbing
_SENSITIVE_KEYS = frozenset({
    "password", "password_hash", "hashed_password",
    "token", "access_token", "refresh_token",
    "secret", "api_key", "private_key",
    "authorization", "jwt",
})


def _scrub_sensitive(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Removes any keys that could contain passwords, tokens, or secrets
    before writing audit detail payloads to the database.
    """
    if not data:
        return data
    return {
        k: "***REDACTED***" if k.lower() in _SENSITIVE_KEYS else v
        for k, v in data.items()
    }


class AuditService:
    """
    System-wide, reusable audit logging service for ADEIP.

    Design goals:
    - Single insert path so all services write through one place.
    - Sensitive field scrubbing enforced at write time.
    - Non-blocking: insert is committed within the caller's existing session.
      The caller controls when the session commits, keeping audit writes
      atomic with the business operation they describe.
    - Querying restricted to authorized roles via the API layer.
    """

    @classmethod
    def log(
        cls,
        db: Session,
        action: AuditAction,
        resource_type: AuditResourceType,
        user_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        flush: bool = False,
    ) -> AuditEvent:
        """
        Appends an audit event to the current database session.

        Args:
            db:            Active SQLAlchemy session.
            action:        Canonical action from AuditAction enum.
            resource_type: Domain from AuditResourceType enum.
            user_id:       Acting user ID (None for system/background events).
            resource_id:   ID of the affected resource (stringified).
            details:       Optional metadata dict. Sensitive keys are auto-scrubbed.
            ip_address:    Request IP address if available.
            flush:         Flush to DB without committing (for use inside larger transactions).
        """
        safe_details = _scrub_sensitive(details)
        serialized = json.dumps(safe_details) if safe_details else None

        event = AuditEvent(
            user_id=user_id,
            action=action.value,
            resource_type=resource_type.value,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=serialized,
            ip_address=ip_address,
        )
        db.add(event)
        if flush:
            db.flush()
        logger.debug(f"AUDIT | {action.value} | resource={resource_type.value}:{resource_id} | user={user_id}")
        return event

    @classmethod
    def query_logs(
        cls,
        db: Session,
        current_user,
        action_filter: Optional[str] = None,
        resource_type_filter: Optional[str] = None,
        user_id_filter: Optional[int] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[List[AuditEvent], int]:
        """
        Queries audit event records with filtering and pagination.
        Restricted to admin and supervisor roles.

        Returns:
            Tuple of (events list, total count).
        """
        if current_user.role not in (UserRole.ADMIN, UserRole.SUPERVISOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Audit log access is restricted to Administrators and Supervisors.",
            )

        stmt = select(AuditEvent)

        if action_filter:
            stmt = stmt.where(AuditEvent.action == action_filter.strip())
        if resource_type_filter:
            stmt = stmt.where(AuditEvent.resource_type == resource_type_filter.strip())
        if user_id_filter is not None:
            stmt = stmt.where(AuditEvent.user_id == user_id_filter)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Apply ordering and pagination
        offset = (max(1, page) - 1) * page_size
        stmt = stmt.order_by(AuditEvent.created_at.desc()).offset(offset).limit(page_size)
        events = list(db.scalars(stmt).all())

        return events, total
