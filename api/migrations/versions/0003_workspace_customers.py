"""Customers created within a guest workspace."""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("workspace_customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("guest_id", sa.String(36), sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False))
    op.create_index("ix_workspace_customers_guest_id", "workspace_customers", ["guest_id"])


def downgrade():
    op.drop_table("workspace_customers")
