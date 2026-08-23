"""
Unit tests for ADEIP Simulated Live Investigation Event Generator (Demonstration System).
"""
import pytest
from app.schemas.simulation import (
    SimulationStartRequest,
    SimulationStatusResponse,
)
from app.services.simulation_service import (
    _SIMULATION_DISCLAIMER,
    _SIMULATION_STEPS,
    SimulationService,
)


def test_simulation_steps_sequence_and_demo_labeling():
    """
    Verify the 6 defined simulation events:
    10:02 CCTV -> 10:03 ACCESS -> 10:04 LOGIN -> 10:05 USB -> 10:07 FILE -> 10:09 NETWORK.
    Must all be explicitly labeled as demo/simulated data.
    """
    assert len(_SIMULATION_STEPS) == 6

    expected_sequence = [
        ("10:02", "CCTV_EVENT"),
        ("10:03", "ACCESS_EVENT"),
        ("10:04", "USER_LOGIN"),
        ("10:05", "USB_CONNECTED"),
        ("10:07", "FILE_ACCESSED"),
        ("10:09", "NETWORK_TRANSFER"),
    ]

    for idx, (expected_time, expected_label) in enumerate(expected_sequence):
        step = _SIMULATION_STEPS[idx]
        assert step["time_str"] == expected_time
        assert step["event_label"] == expected_label
        assert step["metadata"]["is_simulated"] is True
        assert step["metadata"]["simulation_tag"] == "DEMO_CASE_SIMULATION"


def test_simulation_status_response_schema():
    """Verify that status responses clearly convey simulation disclaimers."""
    resp = SimulationStatusResponse(
        case_id=99,
        status="idle",
        is_simulated=True,
        events_generated=0,
        total_events=6,
    )

    assert resp.is_simulated is True
    assert "DEMONSTRATION ONLY" in resp.disclaimer
    assert "Not real police data" in resp.disclaimer


def test_simulation_service_status_query():
    """Querying status for a case with no active run should return idle status."""
    status_resp = SimulationService.get_simulation_status(case_id=888)
    assert status_resp.case_id == 888
    assert status_resp.status in ["idle", "stopped", "completed", "running"]
    assert status_resp.is_simulated is True
