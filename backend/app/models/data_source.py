import datetime
import enum
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SourceType(str, enum.Enum):
    FILE_UPLOAD = "file_upload"
    CCTV_STREAM = "cctv_stream"
    SYSTEM_LOG = "system_log"
    NETWORK_LOG = "network_log"
    CSV_SOURCE = "csv_source"
    JSON_SOURCE = "json_source"
    API = "api"
    WEBHOOK = "webhook"


class SourceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROCESSING = "processing"
    ERROR = "error"
    OFFLINE = "offline"


class DataSource(Base):
    """
    SQLAlchemy ORM model for authorized data sources connected to an investigation case.
    Stores metadata, source credentials/configs (secrets masked), and operational status.
    """
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("investigation_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    # Encrypted / JSON configuration string for credentials, stream URLs, connection parameters
    configuration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus, name="source_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=SourceStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    
    last_seen_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    case = relationship("InvestigationCase", foreign_keys=[case_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<DataSource id={self.id} name={self.source_name} type={self.source_type} status={self.status}>"
