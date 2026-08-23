"""create processing_jobs table

Revision ID: 007_create_processing_jobs_table
Revises: 006_create_investigation_events_table
Create Date: 2026-08-21 14:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "007_create_processing_jobs_table"
down_revision: Union[str, None] = "006_create_investigation_events_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

job_status_enum = sa.Enum(
    "queued",
    "processing",
    "completed",
    "failed",
    name="job_status_enum",
)


def upgrade() -> None:
    job_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("status", job_status_enum, nullable=False, server_default="queued"),
        sa.Column("events_extracted", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_task_id"),
    )
    op.create_index(op.f("ix_processing_jobs_id"), "processing_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_celery_task_id"), "processing_jobs", ["celery_task_id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_evidence_id"), "processing_jobs", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_processing_jobs_requested_by"), "processing_jobs", ["requested_by"], unique=False)
    op.create_index(op.f("ix_processing_jobs_status"), "processing_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_processing_jobs_status"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_requested_by"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_evidence_id"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_celery_task_id"), table_name="processing_jobs")
    op.drop_index(op.f("ix_processing_jobs_id"), table_name="processing_jobs")
    op.drop_table("processing_jobs")
    job_status_enum.drop(op.get_bind(), checkfirst=True)
