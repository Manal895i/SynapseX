"""
InvestigationEvent ORM model for ADEIP.
Stores normalized events parsed from digital evidence artifacts.
"""
import datetime
import enum
from typing import Any, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class EventType(str, enum.Enum):
    """
    Normalized event classification types across heterogeneous evidence formats.
    """
    LOG_ENTRY          = "log_entry"
    AUTH_EVENT         = "auth_event"
    FILE_OPERATION     = "file_operation"
    NETWORK_CONNECTION = "network_connection"
    SYSTEM_METRIC      = "system_metric"
    MEDIA_REGISTERED   = "media_registered"
    ALERT              = "alert"
    OTHER              = "other"


class InvestigationEvent(Base):
    """
    SQLAlchemy ORM model representing a normalized atomic event extracted
    from an evidence source artifact.
    """
    __tablename__ = "investigation_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )

    # Timestamp extracted from the source (nullable — not all events have one)
    timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Where the data came from (e.g. original filename, column name, log channel)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Named entity extracted from the event (e.g. "ip_address", "username", "hostname")
    entity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    entity_value: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, index=True)

    # Full raw content or JSON-serialized structured data for this event
    # Mapped to underlying SQL column 'metadata'
    event_metadata: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    case = relationship("InvestigationCase", foreign_keys=[case_id], lazy="select")
    evidence = relationship("Evidence", foreign_keys=[evidence_id], lazy="select")

    def __init__(self, *args: Any, **kwargs: Any):
        # Support passing metadata as kwarg without conflicting with DeclarativeBase
        if "metadata" in kwargs and "event_metadata" not in kwargs:
            kwargs["event_metadata"] = kwargs.pop("metadata")
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"<InvestigationEvent id={self.id} type={self.event_type} "
            f"evidence_id={self.evidence_id} ts={self.timestamp}>"
        )
