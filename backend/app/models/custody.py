import enum
import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CustodyAction(str, enum.Enum):
    """
    Enumeration of all recognized forensic chain-of-custody actions.
    Each value represents a discrete, auditable lifecycle event.
    """
    EVIDENCE_UPLOADED = "evidence_uploaded"
    INTEGRITY_VERIFIED = "integrity_verified"
    EVIDENCE_VIEWED = "evidence_viewed"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    ANALYSIS_REQUESTED = "analysis_requested"
    REPORT_GENERATED = "report_generated"


class ChainOfCustody(Base):
    """
    Immutable forensic chain-of-custody record for a piece of evidence.

    Records are append-only at the application layer — no UPDATE or DELETE
    operations are exposed to standard users. This ensures the chain remains
    tamper-evident and admissible.
    """
    __tablename__ = "chain_of_custody"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    evidence_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,   # nullable to allow system-generated events
        index=True,
    )
    action: Mapped[CustodyAction] = mapped_column(
        Enum(CustodyAction, name="custody_action_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    evidence = relationship("Evidence", foreign_keys=[evidence_id], lazy="joined")
    actor = relationship("User", foreign_keys=[actor_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<ChainOfCustody id={self.id} evidence_id={self.evidence_id} action={self.action}>"
