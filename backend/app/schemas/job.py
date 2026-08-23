import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.processing_job import JobStatus


class ProcessingJobResponse(BaseModel):
    """Safe public representation of a background processing job."""
    id: int
    celery_task_id: Optional[str] = None
    evidence_id: int
    requested_by: Optional[int] = None
    requester_name: Optional[str] = None
    status: JobStatus
    events_extracted: Optional[int] = None
    # Error message is included for transparency — but must be scrubbed of secrets before storage
    error_message: Optional[str] = None
    queued_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessingStatusResponse(BaseModel):
    """Full processing status response for a given evidence artifact."""
    evidence_id: int
    evidence_number: str
    original_filename: str
    processing_status: str     # Evidence.processing_status
    latest_job: Optional[ProcessingJobResponse] = None
    total_jobs: int
