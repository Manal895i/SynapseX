"""
WebSocket Authentication and Case Authorization Dependencies for ADEIP.

Security Requirements:
1. Authenticate WebSocket connections via JWT token in query parameter or headers.
2. Verify user has access to the target case according to ADEIP RBAC rules.
3. Reject unauthorized connections with WebSocket close code 1008 (Policy Violation).
"""
import logging
from typing import Optional, Tuple
from fastapi import Query, WebSocket, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.case import InvestigationCase
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

logger = logging.getLogger("adeip.websocket.auth")

# Allowed roles with universal case read/write access
_GLOBAL_ACCESS_ROLES = {UserRole.ADMIN, UserRole.SUPERVISOR}


async def authenticate_ws_connection(
    websocket: WebSocket,
    case_id: int,
    token: Optional[str] = Query(None),
) -> Tuple[Optional[User], Optional[InvestigationCase]]:
    """
    Authenticates an incoming WebSocket connection and verifies case-level access permissions.
    Extracts the JWT token from the query parameter (?token=...) or headers.

    Returns (User, InvestigationCase) if authorized, or closes the socket and returns (None, None).
    """
    # 1. Extract Token
    jwt_token = token
    if not jwt_token:
        # Check Sec-WebSocket-Protocol or Authorization header
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:]

    if not jwt_token:
        logger.warning(f"[WebSocketAuth] Connection rejected for Case #{case_id}: Missing authentication token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token.")
        return None, None

    # 2. Decode Token
    payload = AuthService.decode_access_token(jwt_token)
    if not payload:
        logger.warning(f"[WebSocketAuth] Connection rejected for Case #{case_id}: Invalid or expired JWT token.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token.")
        return None, None

    db: Session = SessionLocal()
    try:
        # 3. Lookup User
        user = db.scalars(select(User).where(User.id == payload.user_id)).first()
        if not user or not user.is_active:
            logger.warning(f"[WebSocketAuth] Connection rejected: User #{payload.user_id} not found or inactive.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User inactive or not found.")
            return None, None

        # 4. Verify Case Exists
        case = db.scalars(select(InvestigationCase).where(InvestigationCase.id == case_id)).first()
        if not case:
            logger.warning(f"[WebSocketAuth] Connection rejected: Case #{case_id} not found.")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=f"Case #{case_id} not found.")
            return None, None

        # 5. Check Case-Level Authorization
        # Admins & Supervisors have full platform access; Investigators/Analysts/Viewers have authorized access
        if user.role not in _GLOBAL_ACCESS_ROLES:
            # Check if user is creator or assigned (investigator/analyst/viewer)
            if case.created_by != user.id and user.role not in {UserRole.INVESTIGATOR, UserRole.ANALYST, UserRole.VIEWER}:
                logger.warning(f"[WebSocketAuth] Connection rejected: User #{user.id} lacks access to Case #{case_id}.")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access to this case is unauthorized.")
                return None, None

        return user, case

    finally:
        db.close()
