"""create extracted_entities table

Revision ID: 009_create_extracted_entities_table
Revises: 008_create_analysis_jobs_table
Create Date: 2026-08-21 15:04:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "009_create_extracted_entities_table"
down_revision: Union[str, None] = "008_create_analysis_jobs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

entity_type_enum = sa.Enum(
    "person",
    "device",
    "user_account",
    "ip_address",
    "file",
    "usb_device",
    "location",
    "file_hash",
    "domain",
    "network_port",
    "generic",
    name="entity_type_enum",
)


def upgrade() -> None:
    entity_type_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "extracted_entities",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("entity_type", entity_type_enum, nullable=False),
        sa.Column("entity_value", sa.String(512), nullable=False),
        sa.Column("normalized_value", sa.String(512), nullable=False),
        sa.Column("extraction_method", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["investigation_events.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_extracted_entities_id"), "extracted_entities", ["id"], unique=False)
    op.create_index(op.f("ix_extracted_entities_case_id"), "extracted_entities", ["case_id"], unique=False)
    op.create_index(op.f("ix_extracted_entities_evidence_id"), "extracted_entities", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_extracted_entities_event_id"), "extracted_entities", ["event_id"], unique=False)
    op.create_index(op.f("ix_extracted_entities_entity_type"), "extracted_entities", ["entity_type"], unique=False)
    op.create_index(op.f("ix_extracted_entities_entity_value"), "extracted_entities", ["entity_value"], unique=False)
    op.create_index(op.f("ix_extracted_entities_normalized_value"), "extracted_entities", ["normalized_value"], unique=False)
    op.create_index(op.f("ix_extracted_entities_extraction_method"), "extracted_entities", ["extraction_method"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_extracted_entities_extraction_method"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_normalized_value"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_entity_value"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_entity_type"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_event_id"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_evidence_id"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_case_id"), table_name="extracted_entities")
    op.drop_index(op.f("ix_extracted_entities_id"), table_name="extracted_entities")
    op.drop_table("extracted_entities")
    entity_type_enum.drop(op.get_bind(), checkfirst=True)
