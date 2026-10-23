"""Guest-owned drafts, editable lines and immutable confirmed snapshots."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("guest_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.Integer(), nullable=False))
    op.create_index("ix_guest_sessions_expires_at", "guest_sessions", ["expires_at"])
    op.create_table("drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("guest_id", sa.String(36), sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_email", sa.Text(), nullable=False),
        sa.Column("initial_values", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False))
    op.create_index("ix_drafts_guest_id", "drafts", ["guest_id"])
    op.create_table("draft_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.UniqueConstraint("draft_id", "position"))
    op.create_index("ix_draft_lines_draft_id", "draft_lines", ["draft_id"])
    op.create_table("confirmed_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), sa.ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("guest_id", sa.String(36), sa.ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.String(40), nullable=False, unique=True),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("confirmed_at", sa.Integer(), nullable=False))
    op.create_index("ix_confirmed_orders_guest_id", "confirmed_orders", ["guest_id"])


def downgrade():
    op.drop_table("confirmed_orders")
    op.drop_table("draft_lines")
    op.drop_table("drafts")
    op.drop_table("guest_sessions")
