"""Initial durable session queue and audit event schema."""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("target", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("strategy", sa.String(16), nullable=False),
        sa.Column("budget", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("owner", sa.String(36)),
        sa.Column("result", sa.JSON()),
    )
    op.create_index("ix_sessions_status_created", "discovery_sessions", ["status", "created_at"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_session_id", "audit_events", ["session_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("discovery_sessions")
