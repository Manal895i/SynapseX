"""create investigation_cases table

Revision ID: 002_create_cases_table
Revises: 001_create_users_table
Create Date: 2026-08-21 14:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_create_cases_table"
down_revision: Union[str, None] = "001_create_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

case_status_enum = sa.Enum("active", "under_review", "closed", "archived", name="case_status_enum")
case_priority_enum = sa.Enum("low", "medium", "high", "critical", name="case_priority_enum")


def upgrade() -> None:
    op.create_table(
        "investigation_cases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_number", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", case_status_enum, nullable=False, server_default="active"),
        sa.Column("priority", case_priority_enum, nullable=False, server_default="medium"),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_investigation_cases_case_number"), "investigation_cases", ["case_number"], unique=True)
    op.create_index(op.f("ix_investigation_cases_title"), "investigation_cases", ["title"], unique=False)
    op.create_index(op.f("ix_investigation_cases_id"), "investigation_cases", ["id"], unique=False)
    op.create_index(op.f("ix_investigation_cases_created_by"), "investigation_cases", ["created_by"], unique=False)
    op.create_index(op.f("ix_investigation_cases_assigned_to_id"), "investigation_cases", ["assigned_to_id"], unique=False)
    op.create_index(op.f("ix_investigation_cases_status"), "investigation_cases", ["status"], unique=False)
    op.create_index(op.f("ix_investigation_cases_priority"), "investigation_cases", ["priority"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigation_cases_priority"), table_name="investigation_cases")
    op.drop_index(op.f("ix_investigation_cases_status"), table_name="investigation_cases")
    op.drop_index(op.f("ix_investigation_cases_assigned_to_id"), table_name="investigation_cases")
    op.drop_index(op.f("ix_investigation_cases_created_by"), table_name="investigation_cases")
    op.drop_index(op.f("ix_investigation_cases_id"), table_name="investigation_cases")
    op.drop_index(op.f("ix_investigation_cases_title"), table_name="investigation_cases")
    op.drop_index(op.f("ix_investigation_cases_case_number"), table_name="investigation_cases")
    op.drop_table("investigation_cases")
    case_priority_enum.drop(op.get_bind(), checkfirst=True)
    case_status_enum.drop(op.get_bind(), checkfirst=True)
