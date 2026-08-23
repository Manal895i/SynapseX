"""create investigation_recommendations table

Revision ID: 012_create_investigation_recommendations_table
Revises: 011_create_investigation_findings_table
Create Date: 2026-08-21 23:26:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "012_create_investigation_recommendations_table"
down_revision: Union[str, None] = "011_create_investigation_findings_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

recommendation_priority_enum = sa.Enum(
    "critical",
    "high",
    "medium",
    "low",
    name="recommendation_priority_enum",
)


def upgrade() -> None:
    recommendation_priority_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "investigation_recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recommendation_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("recommendation", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("gap_type", sa.String(64), nullable=False),
        sa.Column("priority", recommendation_priority_enum, nullable=False, server_default="medium"),
        sa.Column("related_finding_id", sa.String(64), nullable=True),
        sa.Column("related_evidence_ids", sa.Text(), nullable=True),
        sa.Column("suggested_source", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recommendation_id"),
    )
    op.create_index(op.f("ix_investigation_recommendations_id"), "investigation_recommendations", ["id"], unique=False)
    op.create_index(op.f("ix_investigation_recommendations_recommendation_id"), "investigation_recommendations", ["recommendation_id"], unique=True)
    op.create_index(op.f("ix_investigation_recommendations_case_id"), "investigation_recommendations", ["case_id"], unique=False)
    op.create_index(op.f("ix_investigation_recommendations_gap_type"), "investigation_recommendations", ["gap_type"], unique=False)
    op.create_index(op.f("ix_investigation_recommendations_priority"), "investigation_recommendations", ["priority"], unique=False)
    op.create_index(op.f("ix_investigation_recommendations_related_finding_id"), "investigation_recommendations", ["related_finding_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_recommendations_related_finding_id"), table_name="investigation_recommendations")
    op.drop_index(op.f("ix_investigation_recommendations_priority"), table_name="investigation_recommendations")
    op.drop_index(op.f("ix_investigation_recommendations_gap_type"), table_name="investigation_recommendations")
    op.drop_index(op.f("ix_investigation_recommendations_case_id"), table_name="investigation_recommendations")
    op.drop_index(op.f("ix_investigation_recommendations_recommendation_id"), table_name="investigation_recommendations")
    op.drop_index(op.f("ix_investigation_recommendations_id"), table_name="investigation_recommendations")
    op.drop_table("investigation_recommendations")
    recommendation_priority_enum.drop(op.get_bind(), checkfirst=True)
