"""Initial LikeGirl schema. All tables use utf8mb4 under MySQL."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None


def upgrade():
    options = {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"}
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        **options,
    )
    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        *[
            sa.Column(name, sa.String(length), nullable=False)
            for name, length in [
                ("title", 80),
                ("subtitle", 200),
                ("boy_name", 30),
                ("girl_name", 30),
                ("boy_avatar", 500),
                ("girl_avatar", 500),
                ("cover", 500),
                ("footer_text", 200),
                ("icp", 100),
            ]
        ],
        sa.Column("start_date", sa.DateTime(), nullable=False),
        *[
            sa.Column(name, sa.Text(), nullable=False)
            for name in ["about_intro", "about_story", "about_future"]
        ],
        sa.Column("messages_enabled", sa.Boolean(), nullable=False),
        **options,
    )
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(40), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("cover", sa.String(500), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        **options,
    )
    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("image", sa.String(500), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(100), nullable=False),
        **options,
    )
    op.create_table(
        "wishes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("image", sa.String(500), nullable=False),
        **options,
    )
    op.create_table(
        "gifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image", sa.String(500), nullable=False),
        sa.Column("sender", sa.String(40), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        **options,
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("content", sa.String(1000), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        **options,
    )
    op.create_index("ix_messages_approved", "messages", ["approved"])


def downgrade():
    for table in [
        "messages",
        "gifts",
        "wishes",
        "photos",
        "articles",
        "site_settings",
        "users",
    ]:
        op.drop_table(table)
