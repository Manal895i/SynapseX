"""
Unit tests for ADEIP Real-Time WebSocket Streaming System.
"""
import asyncio
import json
import pytest
from app.core.websocket import (
    CaseConnectionManager,
    InvestigationWebSocketEvent,
    ws_manager,
)


class MockWebSocket:
    """Mock WebSocket client for testing connection lifecycle and broadcasts."""
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.sent_messages = []

    async def accept(self):
        self.accepted = True

    async def close(self, code: int = 1000, reason: str = ""):
        self.closed = True
        self.close_code = code
        self.close_reason = reason

    async def send_text(self, data: str):
        if self.closed:
            raise RuntimeError("Cannot send message on closed socket.")
        self.sent_messages.append(json.loads(data))


def test_websocket_event_enum_completeness():
    """Verify all required real-time event types are defined."""
    required_events = {
        "evidence_uploaded",
        "evidence_processing_started",
        "evidence_processing_completed",
        "new_investigation_event",
        "timeline_updated",
        "correlation_detected",
        "analysis_started",
        "finding_created",
        "agent_status_updated",
    }
    actual_events = {e.value for e in InvestigationWebSocketEvent}
    assert required_events.issubset(actual_events)


@pytest.mark.asyncio
async def test_websocket_connection_and_room_isolation():
    """
    Test CaseConnectionManager connection, welcome message, and strict room isolation:
    Events for Case 101 must NEVER be delivered to Case 202.
    """
    manager = CaseConnectionManager()

    ws_case_101_user_a = MockWebSocket()
    ws_case_101_user_b = MockWebSocket()
    ws_case_202_user_c = MockWebSocket()

    # Connect clients
    await manager.connect(ws_case_101_user_a, case_id=101, user_id=1, user_name="Investigator A")
    await manager.connect(ws_case_101_user_b, case_id=101, user_id=2, user_name="Analyst B")
    await manager.connect(ws_case_202_user_c, case_id=202, user_id=3, user_name="Officer C")

    assert manager.get_active_user_count(101) == 2
    assert manager.get_active_user_count(202) == 1

    # Check connection confirmation event
    assert ws_case_101_user_a.sent_messages[0]["event"] == "connection_established"
    assert ws_case_202_user_c.sent_messages[0]["event"] == "connection_established"

    # Broadcast event to Case 101 ONLY
    await manager.broadcast_to_case(
        case_id=101,
        event_type=InvestigationWebSocketEvent.EVIDENCE_UPLOADED.value,
        data={"evidence_id": 44, "filename": "firewall.csv"},
    )

    # Verify Case 101 users received the event
    assert len(ws_case_101_user_a.sent_messages) == 2
    assert ws_case_101_user_a.sent_messages[1]["event"] == "evidence_uploaded"
    assert ws_case_101_user_a.sent_messages[1]["data"]["evidence_id"] == 44

    assert len(ws_case_101_user_b.sent_messages) == 2
    assert ws_case_101_user_b.sent_messages[1]["event"] == "evidence_uploaded"

    # Verify Case 202 user DID NOT receive the event (Strict Isolation)
    assert len(ws_case_202_user_c.sent_messages) == 1  # Only welcome message


@pytest.mark.asyncio
async def test_websocket_clean_disconnect():
    """Verify that disconnecting clients removes them cleanly without leaking connections."""
    manager = CaseConnectionManager()
    ws_client = MockWebSocket()

    await manager.connect(ws_client, case_id=303, user_id=9, user_name="Detective")
    assert manager.get_active_user_count(303) == 1

    await manager.disconnect(ws_client)
    assert manager.get_active_user_count(303) == 0


@pytest.mark.asyncio
async def test_websocket_dead_socket_pruning_on_broadcast():
    """Dead or broken sockets should be pruned automatically during broadcast."""
    manager = CaseConnectionManager()
    alive_ws = MockWebSocket()
    broken_ws = MockWebSocket()

    await manager.connect(alive_ws, case_id=404, user_id=1)
    await manager.connect(broken_ws, case_id=404, user_id=2)

    # Manually close broken socket
    await broken_ws.close()

    # Broadcast to room
    await manager.broadcast_to_case(
        case_id=404,
        event_type=InvestigationWebSocketEvent.ANALYSIS_STARTED.value,
        data={"analysis_id": 7},
    )

    # Broken socket should have been pruned cleanly
    assert manager.get_active_user_count(404) == 1
    assert alive_ws.sent_messages[-1]["event"] == "analysis_started"
