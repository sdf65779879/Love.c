"""Encrypted system mailbox and delivery audit records."""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"


def upgrade():
    op.create_table(
        "mail_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("host", sa.String(253), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(254), nullable=False),
        sa.Column("from_address", sa.String(254), nullable=False),
        sa.Column("security", sa.String(10), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "mail_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event", sa.String(30), nullable=False),
        sa.Column("recipient", sa.String(254), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("detail", sa.String(200), nullable=False),
        sa.Column("actor", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("mail_deliveries")
    op.drop_table("mail_settings")
