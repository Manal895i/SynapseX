"""
Investigation Recommendation ORM model for ADEIP Forensic Intelligence.

Stores gap analysis recommendations identifying timeline gaps, incomplete correlations,
missing context, and unsupported hypotheses.
"""
import datetime
import enum
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RecommendationPriority(str, enum.Enum):
    """
    Action priority for addressing investigative evidence gaps.
    """
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class InvestigationRecommendationModel(Base):
    """
    SQLAlchemy ORM model for gap analysis recommendations.

    CRITICAL RULE: Recommendations must NEVER be presented as mandatory conclusions.
    Framed as non-mandatory advisory acquisition guidance for the investigator.
    """
    __tablename__ = "investigation_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    recommendation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recommendation: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    gap_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    priority: Mapped[RecommendationPriority] = mapped_column(
        Enum(RecommendationPriority, name="recommendation_priority_enum", values_callable=lambda x: [e.value for e in x]),
        default=RecommendationPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    related_finding_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    related_evidence_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    case = relationship("InvestigationCase", foreign_keys=[case_id], lazy="select")

    def __repr__(self) -> str:
        return f"<InvestigationRecommendation id={self.id} rec_id={self.recommendation_id} priority={self.priority}>"
