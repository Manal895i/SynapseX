"""
Investigation Correlation ORM model for ADEIP Forensic Intelligence.
"""
import datetime
import enum
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CorrelationSignalType(str, enum.Enum):
    """
    Explainable correlation signal taxonomy.
    """
    SAME_DEVICE              = "same_device"
    SAME_USER_ACCOUNT        = "same_user_account"
    SAME_IP_ADDRESS          = "same_ip_address"
    SAME_FILE                = "same_file"
    SHARED_EVIDENCE_CONTEXT  = "shared_evidence_context"
    TIMESTAMP_PROXIMITY      = "timestamp_proximity"
    MULTI_SIGNAL_CONVERGENCE = "multi_signal_convergence"


class InvestigationCorrelation(Base):
    """
    SQLAlchemy ORM model representing an explainable, evidence-backed correlation link.

    CRITICAL RULE: Correlations must never be labeled as proof.
    Standardized wording: "Potential relationship detected".
    """
    __tablename__ = "investigation_correlations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    correlation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.75)

    # JSON-encoded lists of identifiers
    related_event_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_entity_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supporting_evidence_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reasons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    disclaimer: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="Potential relationship detected. Observational correlation does not establish causation or definitive proof.",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    case = relationship("InvestigationCase", foreign_keys=[case_id], lazy="select")

    def __repr__(self) -> str:
        return f"<InvestigationCorrelation id={self.id} corr_id={self.correlation_id} type={self.signal_type} score={self.correlation_score}>"
