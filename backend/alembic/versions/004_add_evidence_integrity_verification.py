"""add evidence integrity verification columns

Revision ID: 004_add_evidence_integrity_verification
Revises: 003_create_evidence_and_audit_tables
Create Date: 2026-08-21 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004_add_evidence_integrity_verification"
down_revision: Union[str, None] = "003_create_evidence_and_audit_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

integrity_status_enum = sa.Enum("unverified", "verified", "hash_mismatch", "file_missing", name="integrity_status_enum")


def upgrade() -> None:
    # 1. Create enum type and add integrity_status column
    integrity_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "evidence",
        sa.Column("integrity_status", integrity_status_enum, nullable=False, server_default="unverified"),
    )
    op.add_column(
        "evidence",
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_evidence_integrity_status"), "evidence", ["integrity_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_integrity_status"), table_name="evidence")
    op.drop_column("evidence", "last_verified_at")
    op.drop_column("evidence", "integrity_status")
    integrity_status_enum.drop(op.get_bind(), checkfirst=True)
