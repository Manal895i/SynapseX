from fastapi import APIRouter, Depends
from app.api.dependencies.rbac import (
    require_admin,
    require_analyst,
    require_investigator,
    require_supervisor,
    require_viewer,
)
from app.models.user import User

router = APIRouter(prefix="/rbac", tags=["RBAC Testing"])


@router.get("/admin", summary="Test Admin Access")
async def test_admin_access(current_user: User = Depends(require_admin)):
    """Only users with 'admin' role can access this endpoint."""
    return {
        "message": "Access granted: Admin privileged zone",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


@router.get("/supervisor", summary="Test Supervisor Access")
async def test_supervisor_access(current_user: User = Depends(require_supervisor)):
    """Supervisors and Admins can review activities and oversee cases."""
    return {
        "message": "Access granted: Supervisor review zone",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


@router.get("/investigator", summary="Test Investigator Access")
async def test_investigator_access(current_user: User = Depends(require_investigator)):
    """Investigators, Supervisors, and Admins can create and manage cases/evidence."""
    return {
        "message": "Access granted: Investigator operational zone",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


@router.get("/analyst", summary="Test Analyst Access")
async def test_analyst_access(current_user: User = Depends(require_analyst)):
    """Analysts, Investigators, Supervisors, and Admins can perform forensic analysis."""
    return {
        "message": "Access granted: Forensic analyst workspace",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


@router.get("/viewer", summary="Test Viewer Access")
async def test_viewer_access(current_user: User = Depends(require_viewer)):
    """Any authenticated platform user with viewer or above has read access."""
    return {
        "message": "Access granted: Read-only viewer zone",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }
