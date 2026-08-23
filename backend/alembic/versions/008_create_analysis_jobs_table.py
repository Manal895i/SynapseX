"""create analysis_jobs table

Revision ID: 008_create_analysis_jobs_table
Revises: 007_create_processing_jobs_table
Create Date: 2026-08-21 14:58:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "008_create_analysis_jobs_table"
down_revision: Union[str, None] = "007_create_processing_jobs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

analysis_status_enum = sa.Enum(
    "queued",
    "running",
    "completed",
    "failed",
    name="analysis_status_enum",
)


def upgrade() -> None:
    analysis_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=True),
        sa.Column("status", analysis_status_enum, nullable=False, server_default="queued"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("state_snapshot", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_jobs_id"), "analysis_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_case_id"), "analysis_jobs", ["case_id"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_requested_by"), "analysis_jobs", ["requested_by"], unique=False)
    op.create_index(op.f("ix_analysis_jobs_status"), "analysis_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_jobs_status"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_requested_by"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_case_id"), table_name="analysis_jobs")
    op.drop_index(op.f("ix_analysis_jobs_id"), table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    analysis_status_enum.drop(op.get_bind(), checkfirst=True)
