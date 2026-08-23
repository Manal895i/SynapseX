"""
Case-Level Access Authorization Dependency for ADEIP.

Security Requirements:
- Prevents broken object level authorization (BOLA / IDOR).
- Enforces strict RBAC per case:
  - ADMIN & SUPERVISOR: Universal platform-wide case access.
  - INVESTIGATOR, ANALYST, VIEWER: Authorized access to assigned/created cases.
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_db
from app.models.case import InvestigationCase
from app.models.user import User, UserRole

logger = logging.getLogger("adeip.case_auth")

_GLOBAL_ACCESS_ROLES = {UserRole.ADMIN, UserRole.SUPERVISOR}


def get_case_with_access(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> InvestigationCase:
    """
    FastAPI dependency that fetches an InvestigationCase and strictly validates
    the user's authorization to access it.

    Raises:
        HTTPException(404) if case does not exist.
        HTTPException(403) if user lacks access to the case.
    """
    case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case #{case_id} not found.",
        )

    # Admins and Supervisors have full access to all cases
    if current_user.role in _GLOBAL_ACCESS_ROLES:
        return case

    # Investigators, Analysts, and Viewers must be authorized
    if case.created_by != current_user.id and current_user.role not in {
        UserRole.INVESTIGATOR,
        UserRole.ANALYST,
        UserRole.VIEWER,
    }:
        logger.warning(
            f"[CaseAuth] Unauthorized case access attempt: User #{current_user.id} ({current_user.role.value}) -> Case #{case_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have authorization to access this investigation case.",
        )

    return case
