"""create investigation_reports table

Revision ID: 013_create_investigation_reports_table
Revises: 012_create_investigation_recommendations_table
Create Date: 2026-08-21 23:36:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "013_create_investigation_reports_table"
down_revision: Union[str, None] = "012_create_investigation_recommendations_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

report_format_enum = sa.Enum(
    "json",
    "html",
    "markdown",
    name="report_format_enum",
)


def upgrade() -> None:
    report_format_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "investigation_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("report_id", sa.String(64), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("report_format", report_format_enum, nullable=False, server_default="html"),
        sa.Column(
            "disclaimer",
            sa.String(255),
            nullable=False,
            server_default="AI-Assisted Draft — Requires Human Investigator Review",
        ),
        sa.Column("report_data", sa.Text(), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=True),
        sa.Column("generated_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["case_id"], ["investigation_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
    )
    op.create_index(op.f("ix_investigation_reports_id"), "investigation_reports", ["id"], unique=False)
    op.create_index(op.f("ix_investigation_reports_report_id"), "investigation_reports", ["report_id"], unique=True)
    op.create_index(op.f("ix_investigation_reports_case_id"), "investigation_reports", ["case_id"], unique=False)
    op.create_index(op.f("ix_investigation_reports_generated_by"), "investigation_reports", ["generated_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_reports_generated_by"), table_name="investigation_reports")
    op.drop_index(op.f("ix_investigation_reports_case_id"), table_name="investigation_reports")
    op.drop_index(op.f("ix_investigation_reports_report_id"), table_name="investigation_reports")
    op.drop_index(op.f("ix_investigation_reports_id"), table_name="investigation_reports")
    op.drop_table("investigation_reports")
    report_format_enum.drop(op.get_bind(), checkfirst=True)
