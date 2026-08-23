import enum
import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class JobStatus(str, enum.Enum):
    """Lifecycle states of a background processing job."""
    QUEUED      = "queued"
    PROCESSING  = "processing"
    COMPLETED   = "completed"
    FAILED      = "failed"


class ProcessingJob(Base):
    """
    Tracks the lifecycle of an asynchronous evidence processing job.

    One record is created per processing request.
    Workers update status, result counts, and error messages through this table.
    This record is the source of truth for job progress — never query Celery directly from routes.
    """
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # The Celery task ID — used to correlate with worker logs
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    evidence_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True,
    )
    events_extracted: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Safe error message — sensitive data must never be stored here
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    queued_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    evidence = relationship("Evidence", foreign_keys=[evidence_id], lazy="joined")
    requester = relationship("User", foreign_keys=[requested_by], lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<ProcessingJob id={self.id} status={self.status} "
            f"evidence_id={self.evidence_id} task={self.celery_task_id}>"
        )
