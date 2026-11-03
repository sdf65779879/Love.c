"""Persistent email challenges and revocable private visitor sessions."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade():
    op.create_table(
        "email_challenges",
        sa.Column("qq", sa.String(11), primary_key=True),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("nonce", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("send_count", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
    )
    op.create_table(
        "visitor_sessions",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("qq", sa.String(11), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("visitor_sessions")
    op.drop_table("email_challenges")
