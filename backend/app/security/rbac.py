import enum
from typing import List, Optional, Set
from fastapi import HTTPException, status
from app.models.user import User, UserRole


class CasePermission(str, enum.Enum):
    """
    Granular permission scopes designed for ADEIP case-level and evidence-level access control.
    """
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"
    CASE_REVIEW = "case:review"
    EVIDENCE_UPLOAD = "evidence:upload"
    EVIDENCE_ANALYZE = "evidence:analyze"
    FINDINGS_ADD = "findings:add"
    FINDINGS_REVIEW = "findings:review"
    ADMIN_MANAGE_USERS = "admin:manage_users"


# Role-to-default-permissions capability matrix
ROLE_PERMISSIONS: dict[UserRole, Set[CasePermission]] = {
    UserRole.ADMIN: {p for p in CasePermission},
    UserRole.SUPERVISOR: {
        CasePermission.CASE_READ,
        CasePermission.CASE_REVIEW,
        CasePermission.FINDINGS_REVIEW,
        CasePermission.EVIDENCE_ANALYZE,
        CasePermission.FINDINGS_ADD,
    },
    UserRole.INVESTIGATOR: {
        CasePermission.CASE_CREATE,
        CasePermission.CASE_READ,
        CasePermission.CASE_UPDATE,
        CasePermission.EVIDENCE_UPLOAD,
        CasePermission.EVIDENCE_ANALYZE,
        CasePermission.FINDINGS_ADD,
    },
    UserRole.ANALYST: {
        CasePermission.CASE_READ,
        CasePermission.EVIDENCE_ANALYZE,
        CasePermission.FINDINGS_ADD,
    },
    UserRole.VIEWER: {
        CasePermission.CASE_READ,
    },
}


class RoleChecker:
    """
    FastAPI dependency callable for role validation.
    Enforces that the current authenticated user possesses one of the authorized roles.
    """

    def __init__(self, allowed_roles: List[UserRole], allow_admin_override: bool = True):
        self.allowed_roles = set(allowed_roles)
        if allow_admin_override:
            self.allowed_roles.add(UserRole.ADMIN)

    def __call__(self, user: User) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: User role '{user.role.value}' does not have permission. Required roles: {[r.value for r in self.allowed_roles]}",
            )
        return user


class CaseAccessEvaluator:
    """
    Extensible interface prepared for upcoming case-level access checks (e.g., assignment, organization boundary).
    """

    @classmethod
    def can_access_case(cls, user: User, case_id: int, required_permission: CasePermission, is_assigned: bool = False) -> bool:
        # Admins have global access
        if user.role == UserRole.ADMIN:
            return True

        # Check if user role inherently has the required permission
        user_perms = ROLE_PERMISSIONS.get(user.role, set())
        if required_permission not in user_perms:
            return False

        # For investigators and analysts, verify assignment when case-level isolation is active
        if user.role in (UserRole.INVESTIGATOR, UserRole.ANALYST):
            return is_assigned or user.role == UserRole.SUPERVISOR

        return True
