"""P0 executable baseline."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "schema_info",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.String(100), nullable=False),
    )


def downgrade():
    op.drop_table("schema_info")
