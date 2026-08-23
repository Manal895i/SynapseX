import pytest
from fastapi import HTTPException
from app.models.user import User, UserRole
from app.security.rbac import CaseAccessEvaluator, CasePermission, RoleChecker, ROLE_PERMISSIONS


def make_mock_user(role: UserRole, is_active: bool = True) -> User:
    user = User(
        id=10,
        full_name="Test Officer",
        email="test.officer@adeip.internal",
        password_hash="hash",
        role=role,
        is_active=is_active,
    )
    return user


def test_admin_role_checker():
    admin_checker = RoleChecker([UserRole.ADMIN], allow_admin_override=False)
    admin_user = make_mock_user(UserRole.ADMIN)
    viewer_user = make_mock_user(UserRole.VIEWER)

    # Admin should succeed
    assert admin_checker(admin_user) == admin_user

    # Viewer should be blocked with 403
    with pytest.raises(HTTPException) as exc:
        admin_checker(viewer_user)
    assert exc.value.status_code == 403


def test_investigator_role_checker_with_admin_override():
    investigator_checker = RoleChecker([UserRole.INVESTIGATOR], allow_admin_override=True)
    investigator_user = make_mock_user(UserRole.INVESTIGATOR)
    admin_user = make_mock_user(UserRole.ADMIN)
    viewer_user = make_mock_user(UserRole.VIEWER)

    assert investigator_checker(investigator_user) == investigator_user
    assert investigator_checker(admin_user) == admin_user

    with pytest.raises(HTTPException) as exc:
        investigator_checker(viewer_user)
    assert exc.value.status_code == 403


def test_case_access_evaluator():
    admin_user = make_mock_user(UserRole.ADMIN)
    supervisor_user = make_mock_user(UserRole.SUPERVISOR)
    investigator_user = make_mock_user(UserRole.INVESTIGATOR)
    viewer_user = make_mock_user(UserRole.VIEWER)

    # Admin can always delete
    assert CaseAccessEvaluator.can_access_case(admin_user, 1, CasePermission.CASE_DELETE) is True

    # Viewer cannot upload evidence
    assert CaseAccessEvaluator.can_access_case(viewer_user, 1, CasePermission.EVIDENCE_UPLOAD) is False

    # Viewer can read cases
    assert CaseAccessEvaluator.can_access_case(viewer_user, 1, CasePermission.CASE_READ) is True

    # Supervisor can review findings
    assert CaseAccessEvaluator.can_access_case(supervisor_user, 1, CasePermission.FINDINGS_REVIEW) is True

    # Investigator assigned to case can upload evidence
    assert CaseAccessEvaluator.can_access_case(investigator_user, 1, CasePermission.EVIDENCE_UPLOAD, is_assigned=True) is True
