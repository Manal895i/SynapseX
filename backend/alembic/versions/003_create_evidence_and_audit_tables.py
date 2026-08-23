"""create evidence and audit_events tables

Revision ID: 003_create_evidence_and_audit_tables
Revises: 002_create_cases_table
Create Date: 2026-08-21 14:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_create_evidence_and_audit_tables"
down_revision: Union[str, None] = "002_create_cases_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

processing_status_enum = sa.Enum("pending", "processing", "completed", "failed", name="processing_status_enum")


def upgrade() -> None:
    # 1. Create Evidence Table
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evidence_number", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column("processing_status", processing_status_enum, nullable=False, server_default="pending"),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_evidence_id"), "evidence", ["id"], unique=False)
    op.create_index(op.f("ix_evidence_evidence_number"), "evidence", ["evidence_number"], unique=True)
    op.create_index(op.f("ix_evidence_case_id"), "evidence", ["case_id"], unique=False)
    op.create_index(op.f("ix_evidence_sha256_hash"), "evidence", ["sha256_hash"], unique=False)
    op.create_index(op.f("ix_evidence_processing_status"), "evidence", ["processing_status"], unique=False)
    op.create_index(op.f("ix_evidence_uploaded_by"), "evidence", ["uploaded_by"], unique=False)

    # 2. Create Audit Events Table
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_id"), "audit_events", ["id"], unique=False)
    op.create_index(op.f("ix_audit_events_user_id"), "audit_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_events_action"), "audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_audit_events_resource_type"), "audit_events", ["resource_type"], unique=False)
    op.create_index(op.f("ix_audit_events_resource_id"), "audit_events", ["resource_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_events_resource_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_resource_type"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_action"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_user_id"), table_name="audit_events")
    op.drop_index(op.f("ix_audit_events_id"), table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index(op.f("ix_evidence_uploaded_by"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_processing_status"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_sha256_hash"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_case_id"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_evidence_number"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_id"), table_name="evidence")
    op.drop_table("evidence")
    processing_status_enum.drop(op.get_bind(), checkfirst=True)
