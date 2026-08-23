"""
Simulation Event Generator Pydantic Schemas for ADEIP.

CRITICAL REQUIREMENT:
All simulation payloads and responses are explicitly labeled as demo/simulated data.
Never presented as real police data.
"""
import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SimulationStartRequest(BaseModel):
    """Configuration parameters for launching a controlled demonstration event sequence."""
    step_delay_seconds: float = Field(
        default=1.5,
        ge=0.1,
        le=10.0,
        description="Delay in seconds between emitting each simulated forensic event",
    )
    auto_correlate: bool = Field(
        default=True,
        description="Whether to automatically trigger correlation analysis upon simulation completion",
    )
    auto_reason: bool = Field(
        default=True,
        description="Whether to automatically trigger the reasoning agent upon simulation completion",
    )


class SimulationStatusResponse(BaseModel):
    """Current status and progress of the demonstration investigation event generator."""
    case_id: int
    status: str = Field(..., description="'idle', 'running', 'completed', 'stopped', 'error'")
    is_simulated: bool = True
    disclaimer: str = "DEMONSTRATION ONLY: Simulated investigation data. Not real police data."
    events_generated: int = 0
    total_events: int = 6
    current_step: Optional[str] = None
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None
    message: str = "Simulated forensic investigation event generator."

    model_config = ConfigDict(from_attributes=True)
