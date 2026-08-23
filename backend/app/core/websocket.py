"""
WebSocket Connection Manager & Real-Time Event System for ADEIP.

Requirements:
1. Isolated Case-Level Rooms: Events are only delivered to authorized connections for that specific case.
2. Robust Disconnect Handling: Removes dead sockets cleanly without leaking memory or throwing unhandled errors.
3. PostgreSQL remains the single source of truth; WebSockets provide ephemeral real-time notifications.
"""
import asyncio
import datetime
import enum
import json
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("adeip.websocket")


class InvestigationWebSocketEvent(str, enum.Enum):
    """
    Standardized real-time forensic event types for WebSocket streaming.
    """
    CONNECTION_ESTABLISHED        = "connection_established"
    EVIDENCE_UPLOADED             = "evidence_uploaded"
    EVIDENCE_PROCESSING_STARTED   = "evidence_processing_started"
    EVIDENCE_PROCESSING_COMPLETED = "evidence_processing_completed"
    NEW_INVESTIGATION_EVENT       = "new_investigation_event"
    TIMELINE_UPDATED              = "timeline_updated"
    CORRELATION_DETECTED          = "correlation_detected"
    ANALYSIS_STARTED              = "analysis_started"
    FINDING_CREATED               = "finding_created"
    AGENT_STATUS_UPDATED          = "agent_status_updated"
    PONG                          = "pong"


class CaseConnectionManager:
    """
    Manages active WebSocket connections grouped by case_id.
    Thread-safe, non-blocking broadcast dispatch with clean connection lifecycle management.
    """

    def __init__(self):
        # case_id -> Set of active WebSocket connections
        self._case_rooms: Dict[int, Set[WebSocket]] = {}
        # websocket -> (case_id, user_id)
        self._socket_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, case_id: int, user_id: int, user_name: str = ""):
        """
        Accepts and registers a new WebSocket connection into the specified case room.
        """
        await websocket.accept()

        async with self._lock:
            if case_id not in self._case_rooms:
                self._case_rooms[case_id] = set()
            self._case_rooms[case_id].add(websocket)
            self._socket_metadata[websocket] = {
                "case_id": case_id,
                "user_id": user_id,
                "user_name": user_name,
                "connected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        logger.info(f"[WebSocket] User #{user_id} ({user_name}) connected to Case #{case_id} room. (Total in room: {len(self._case_rooms[case_id])})")

        # Send initial confirmation event to connected client
        await self.send_personal_message(
            websocket,
            {
                "event": InvestigationWebSocketEvent.CONNECTION_ESTABLISHED.value,
                "case_id": case_id,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "data": {
                    "message": f"Connected to live investigation stream for Case #{case_id}",
                    "user_id": user_id,
                },
            },
        )

    async def disconnect(self, websocket: WebSocket):
        """
        Cleanly unregisters and removes a disconnected WebSocket.
        """
        async with self._lock:
            meta = self._socket_metadata.pop(websocket, None)
            if meta:
                case_id = meta.get("case_id")
                if case_id in self._case_rooms:
                    self._case_rooms[case_id].discard(websocket)
                    if not self._case_rooms[case_id]:
                        del self._case_rooms[case_id]
                logger.info(f"[WebSocket] User #{meta.get('user_id')} disconnected from Case #{case_id}.")

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Sends a structured JSON payload directly to a specific socket."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as exc:
            logger.debug(f"[WebSocket] Failed to send personal message: {exc}")

    async def broadcast_to_case(
        self,
        case_id: int,
        event_type: str,
        data: Dict[str, Any],
    ):
        """
        Broadcasts a structured JSON event to all active connections subscribed to a specific case.
        Dead sockets are automatically pruned.
        """
        async with self._lock:
            sockets = list(self._case_rooms.get(case_id, set()))

        if not sockets:
            logger.debug(f"[WebSocket] No active listeners for Case #{case_id}. Event '{event_type}' buffered/skipped.")
            return

        payload = json.dumps({
            "event": event_type,
            "case_id": case_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data": data,
        })

        dead_sockets = []
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.debug(f"[WebSocket] Dead socket detected during broadcast to Case #{case_id}: {exc}")
                dead_sockets.append(ws)

        if dead_sockets:
            for ws in dead_sockets:
                await self.disconnect(ws)

        logger.info(f"[WebSocket] Broadcasted '{event_type}' to {len(sockets) - len(dead_sockets)} client(s) on Case #{case_id}.")

    def get_active_user_count(self, case_id: int) -> int:
        """Returns the number of active live connections for a given case."""
        return len(self._case_rooms.get(case_id, set()))


# Global singleton WebSocket connection manager
ws_manager = CaseConnectionManager()


def broadcast_case_event(case_id: int, event_type: str, data: Dict[str, Any]):
    """
    Synchronous helper to schedule WebSocket broadcast in the active event loop,
    enabling non-async services to emit live real-time notifications.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(ws_manager.broadcast_to_case(case_id, event_type, data))
    except RuntimeError:
        # No running event loop (e.g. running inside sync unit test thread or celery worker)
        pass
