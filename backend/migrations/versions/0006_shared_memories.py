"""Create travel memories and anniversaries. Preserve the retired modules' tables."""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"


def upgrade():
    op.create_table(
        "places",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("city_id", sa.String(64), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image", sa.String(500), nullable=False),
    )
    op.create_table(
        "anniversaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("annual", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    site = sa.table(
        "site_settings", sa.column("id"), sa.column("card_titles", sa.JSON())
    )
    db = op.get_bind()
    for row in db.execute(sa.select(site)).mappings().all():
        titles = dict(row["card_titles"] or {})
        for retired in ("/messages", "/gifts"):
            titles.pop(retired, None)
        db.execute(
            site.update().where(site.c.id == row["id"]).values(card_titles=titles)
        )


def downgrade():
    op.drop_table("anniversaries")
    op.drop_table("places")
