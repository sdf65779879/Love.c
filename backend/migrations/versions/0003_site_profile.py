"""Add configurable branding and QQ couple profiles, preserving existing settings."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    op.add_column(
        "site_settings",
        sa.Column("logo_text", sa.String(80), nullable=False, server_default=""),
    )
    op.add_column(
        "site_settings",
        sa.Column(
            "avatar_blur", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column("site_settings", sa.Column("card_titles", sa.JSON(), nullable=True))
    table = sa.table("site_settings", sa.column("card_titles", sa.JSON()))
    op.execute(table.update().values(card_titles={}))
    with op.batch_alter_table("site_settings") as batch:
        batch.alter_column("card_titles", existing_type=sa.JSON(), nullable=False)
    for name in ("boy_qq", "girl_qq"):
        op.add_column(
            "site_settings",
            sa.Column(name, sa.String(11), nullable=False, server_default=""),
        )


def downgrade():
    for name in ("girl_qq", "boy_qq", "card_titles", "avatar_blur", "logo_text"):
        op.drop_column("site_settings", name)
