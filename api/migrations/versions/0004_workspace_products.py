"""Products created within a guest workspace."""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("workspace_products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("guest_id", sa.String(36), sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("pack_size", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("stock_cases", sa.Integer(), nullable=False),
        sa.UniqueConstraint("guest_id", "sku"))
    op.create_index("ix_workspace_products_guest_id", "workspace_products", ["guest_id"])


def downgrade():
    op.drop_table("workspace_products")
