"""create investigation_events table

Revision ID: 006_create_investigation_events_table
Revises: 005_create_chain_of_custody_table
Create Date: 2026-08-21 14:43:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "006_create_investigation_events_table"
down_revision: Union[str, None] = "005_create_chain_of_custody_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

event_type_enum = sa.Enum(
    "structured_row",
    "json_record",
    "log_entry",
    "windows_event",
    "media_registered",
    "binary_registered",
    "generic",
    name="event_type_enum",
)


def upgrade() -> None:
    event_type_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "investigation_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("event_type", event_type_enum, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("entity_type", sa.String(64), nullable=True),
        sa.Column("entity_value", sa.String(512), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_investigation_events_id"), "investigation_events", ["id"], unique=False)
    op.create_index(op.f("ix_investigation_events_case_id"), "investigation_events", ["case_id"], unique=False)
    op.create_index(op.f("ix_investigation_events_evidence_id"), "investigation_events", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_investigation_events_event_type"), "investigation_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_investigation_events_timestamp"), "investigation_events", ["timestamp"], unique=False)
    op.create_index(op.f("ix_investigation_events_entity_type"), "investigation_events", ["entity_type"], unique=False)
    op.create_index(op.f("ix_investigation_events_entity_value"), "investigation_events", ["entity_value"], unique=False)
    op.create_index(op.f("ix_investigation_events_source"), "investigation_events", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_events_source"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_entity_value"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_entity_type"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_timestamp"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_event_type"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_evidence_id"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_case_id"), table_name="investigation_events")
    op.drop_index(op.f("ix_investigation_events_id"), table_name="investigation_events")
    op.drop_table("investigation_events")
    event_type_enum.drop(op.get_bind(), checkfirst=True)
