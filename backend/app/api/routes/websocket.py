"""
WebSocket Routes for ADEIP Live Investigation Streaming.

Endpoints:
- /ws/cases/{case_id}: Authenticated real-time WebSocket channel for case events.
"""
import datetime
import json
import logging
from typing import Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.dependencies.websocket_auth import authenticate_ws_connection
from app.core.websocket import InvestigationWebSocketEvent, ws_manager

logger = logging.getLogger("adeip.websocket.routes")

router = APIRouter(tags=["Live Investigation WebSockets"])


@router.websocket("/ws/cases/{case_id}")
async def case_live_investigation_stream(
    websocket: WebSocket,
    case_id: int,
    token: Optional[str] = Query(None, description="JWT Authentication Token"),
):
    """
    Real-time WebSocket stream for a digital investigation case:
    - **Authentication**: Validates JWT token from query parameter or authorization header.
    - **Authorization**: Ensures the user has permissions to view the specified case.
    - **Isolation**: Messages from other cases are never leaked across channels.
    - **Events Streamed**:
      - `evidence_uploaded`
      - `evidence_processing_started`
      - `evidence_processing_completed`
      - `new_investigation_event`
      - `timeline_updated`
      - `correlation_detected`
      - `analysis_started`
      - `finding_created`
      - `agent_status_updated`
    """
    # 1. Authenticate and Authorize Connection
    user, case = await authenticate_ws_connection(websocket=websocket, case_id=case_id, token=token)
    if not user or not case:
        return  # Socket already closed with 1008 policy violation by dependency

    # 2. Register Connection in Case Room
    await ws_manager.connect(
        websocket=websocket,
        case_id=case_id,
        user_id=user.id,
        user_name=user.full_name,
    )

    # 3. Client Listener Loop (Heartbeat & Incoming Message Handling)
    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                msg_data = json.loads(raw_message)
                action = msg_data.get("action") or msg_data.get("event")

                # Handle Client Ping / Heartbeat
                if action == "ping":
                    await ws_manager.send_personal_message(
                        websocket,
                        {
                            "event": InvestigationWebSocketEvent.PONG.value,
                            "case_id": case_id,
                            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        },
                    )

            except json.JSONDecodeError:
                # Ignore non-JSON text frames
                pass

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as exc:
        logger.debug(f"[WebSocket] Socket closed with exception on Case #{case_id}: {exc}")
        await ws_manager.disconnect(websocket)
