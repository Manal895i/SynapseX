"""
Analysis Job ORM model for ADEIP AI Multi-Agent Investigations.
"""
import enum
import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AnalysisStatus(str, enum.Enum):
    """Lifecycle states of an AI Multi-Agent analysis run."""
    QUEUED      = "queued"
    RUNNING     = "running"
    COMPLETED   = "completed"
    FAILED      = "failed"


class AnalysisJob(Base):
    """
    SQLAlchemy ORM model representing an AI Multi-Agent investigation run on a case.
    Stores the full investigation state snapshot, synthesized findings, and diagnostic logs.
    """
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysis_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=AnalysisStatus.QUEUED,
        nullable=False,
        index=True,
    )

    # High-level executive summary / briefing output
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON-serialized snapshot of the complete InvestigationState
    state_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    case = relationship("InvestigationCase", foreign_keys=[case_id], lazy="joined")
    requester = relationship("User", foreign_keys=[requested_by], lazy="joined")

    def __repr__(self) -> str:
        return f"<AnalysisJob id={self.id} case_id={self.case_id} status={self.status}>"
