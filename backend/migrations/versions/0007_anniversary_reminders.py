"""Reserve one email per recipient and anniversary occurrence."""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"


def upgrade():
    op.add_column(
        "mail_deliveries", sa.Column("reminder_key", sa.String(64), nullable=True)
    )
    op.create_index(
        "uq_mail_reminder", "mail_deliveries", ["reminder_key"], unique=True
    )


def downgrade():
    op.drop_index("uq_mail_reminder", table_name="mail_deliveries")
    op.drop_column("mail_deliveries", "reminder_key")
