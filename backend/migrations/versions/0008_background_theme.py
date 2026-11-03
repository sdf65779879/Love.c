"""Preserve the original cream background for existing sites."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"


def upgrade():
    op.add_column(
        "site_settings",
        sa.Column("background_theme", sa.String(16), nullable=False, server_default="cream"),
    )


def downgrade():
    op.drop_column("site_settings", "background_theme")
