"""create investigation_correlations table

Revision ID: 010_create_investigation_correlations_table
Revises: 009_create_extracted_entities_table
Create Date: 2026-08-21 15:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "010_create_investigation_correlations_table"
down_revision: Union[str, None] = "009_create_extracted_entities_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investigation_correlations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("signal_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("correlation_score", sa.Float(), nullable=False, server_default="0.75"),
        sa.Column("related_event_ids", sa.Text(), nullable=True),
        sa.Column("related_entity_ids", sa.Text(), nullable=True),
        sa.Column("supporting_evidence_ids", sa.Text(), nullable=True),
        sa.Column("reasons", sa.Text(), nullable=True),
        sa.Column(
            "disclaimer",
            sa.String(512),
            nullable=False,
            server_default="Potential relationship detected. Observational correlation does not establish causation or definitive proof.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_investigation_correlations_id"), "investigation_correlations", ["id"], unique=False)
    op.create_index(op.f("ix_investigation_correlations_case_id"), "investigation_correlations", ["case_id"], unique=False)
    op.create_index(op.f("ix_investigation_correlations_correlation_id"), "investigation_correlations", ["correlation_id"], unique=False)
    op.create_index(op.f("ix_investigation_correlations_signal_type"), "investigation_correlations", ["signal_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_correlations_signal_type"), table_name="investigation_correlations")
    op.drop_index(op.f("ix_investigation_correlations_correlation_id"), table_name="investigation_correlations")
    op.drop_index(op.f("ix_investigation_correlations_case_id"), table_name="investigation_correlations")
    op.drop_index(op.f("ix_investigation_correlations_id"), table_name="investigation_correlations")
    op.drop_table("investigation_correlations")
