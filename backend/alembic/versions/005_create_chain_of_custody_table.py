"""create chain_of_custody table

Revision ID: 005_create_chain_of_custody_table
Revises: 004_add_evidence_integrity_verification
Create Date: 2026-08-21 14:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005_create_chain_of_custody_table"
down_revision: Union[str, None] = "004_add_evidence_integrity_verification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

custody_action_enum = sa.Enum(
    "evidence_uploaded",
    "integrity_verified",
    "evidence_viewed",
    "processing_started",
    "processing_completed",
    "analysis_requested",
    "report_generated",
    name="custody_action_enum",
)


def upgrade() -> None:
    custody_action_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "chain_of_custody",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", custody_action_enum, nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chain_of_custody_id"), "chain_of_custody", ["id"], unique=False)
    op.create_index(op.f("ix_chain_of_custody_evidence_id"), "chain_of_custody", ["evidence_id"], unique=False)
    op.create_index(op.f("ix_chain_of_custody_actor_id"), "chain_of_custody", ["actor_id"], unique=False)
    op.create_index(op.f("ix_chain_of_custody_action"), "chain_of_custody", ["action"], unique=False)
    op.create_index(op.f("ix_chain_of_custody_created_at"), "chain_of_custody", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_chain_of_custody_created_at"), table_name="chain_of_custody")
    op.drop_index(op.f("ix_chain_of_custody_action"), table_name="chain_of_custody")
    op.drop_index(op.f("ix_chain_of_custody_actor_id"), table_name="chain_of_custody")
    op.drop_index(op.f("ix_chain_of_custody_evidence_id"), table_name="chain_of_custody")
    op.drop_index(op.f("ix_chain_of_custody_id"), table_name="chain_of_custody")
    op.drop_table("chain_of_custody")
    custody_action_enum.drop(op.get_bind(), checkfirst=True)
