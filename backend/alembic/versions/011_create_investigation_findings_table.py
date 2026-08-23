"""create investigation_findings table

Revision ID: 011_create_investigation_findings_table
Revises: 010_create_investigation_correlations_table
Create Date: 2026-08-21 23:18:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "011_create_investigation_findings_table"
down_revision: Union[str, None] = "010_create_investigation_correlations_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

finding_review_status_enum = sa.Enum(
    "pending_review",
    "accepted_as_lead",
    "rejected",
    "needs_more_analysis",
    name="finding_review_status_enum",
)


def upgrade() -> None:
    finding_review_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "investigation_findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("finding_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.85"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("observations", sa.Text(), nullable=False),
        sa.Column("potential_hypotheses", sa.Text(), nullable=False),
        sa.Column("supporting_evidence_ids", sa.Text(), nullable=False),
        sa.Column("supporting_event_ids", sa.Text(), nullable=False),
        sa.Column("alternative_explanations", sa.Text(), nullable=False),
        sa.Column("recommended_verification", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=False),
        sa.Column("review_status", finding_review_status_enum, nullable=False, server_default="pending_review"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finding_id"),
    )
    op.create_index(op.f("ix_investigation_findings_id"), "investigation_findings", ["id"], unique=False)
    op.create_index(op.f("ix_investigation_findings_finding_id"), "investigation_findings", ["finding_id"], unique=True)
    op.create_index(op.f("ix_investigation_findings_case_id"), "investigation_findings", ["case_id"], unique=False)
    op.create_index(op.f("ix_investigation_findings_category"), "investigation_findings", ["category"], unique=False)
    op.create_index(op.f("ix_investigation_findings_review_status"), "investigation_findings", ["review_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_findings_review_status"), table_name="investigation_findings")
    op.drop_index(op.f("ix_investigation_findings_category"), table_name="investigation_findings")
    op.drop_index(op.f("ix_investigation_findings_case_id"), table_name="investigation_findings")
    op.drop_index(op.f("ix_investigation_findings_finding_id"), table_name="investigation_findings")
    op.drop_index(op.f("ix_investigation_findings_id"), table_name="investigation_findings")
    op.drop_table("investigation_findings")
    finding_review_status_enum.drop(op.get_bind(), checkfirst=True)
