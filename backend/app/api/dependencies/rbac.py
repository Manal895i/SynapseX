from typing import Callable, Sequence
from fastapi import Depends

from app.api.dependencies.auth import get_current_active_user
from app.models.user import User, UserRole
from app.security.rbac import RoleChecker


def require_roles(*allowed_roles: UserRole, allow_admin_override: bool = True) -> Callable[[User], User]:
    """
    Factory creating a FastAPI dependency that checks if the active user
    has one of the specified roles.
    """
    checker = RoleChecker(list(allowed_roles), allow_admin_override=allow_admin_override)

    def role_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        return checker(current_user)

    return role_dependency


# Common reusable role gate dependencies
require_admin = require_roles(UserRole.ADMIN, allow_admin_override=False)
require_supervisor = require_roles(UserRole.SUPERVISOR, UserRole.ADMIN)
require_investigator = require_roles(UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMIN)
require_analyst = require_roles(UserRole.ANALYST, UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMIN)
require_viewer = require_roles(UserRole.VIEWER, UserRole.ANALYST, UserRole.INVESTIGATOR, UserRole.SUPERVISOR, UserRole.ADMIN)
