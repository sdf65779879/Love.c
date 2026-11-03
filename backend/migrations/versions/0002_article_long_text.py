"""Allow 50,000 Unicode characters in a story, including emoji."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import MEDIUMTEXT

revision = "0002"
down_revision = "0001"


def upgrade():
    if op.get_bind().dialect.name == "mysql":
        op.alter_column(
            "articles",
            "content",
            existing_type=sa.Text(),
            type_=MEDIUMTEXT(),
            existing_nullable=False,
        )


def downgrade():
    if op.get_bind().dialect.name == "mysql":
        op.alter_column(
            "articles",
            "content",
            existing_type=MEDIUMTEXT(),
            type_=sa.Text(),
            existing_nullable=False,
        )
