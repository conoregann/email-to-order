"""Validated extraction provenance and durable provider attempts."""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("drafts", sa.Column("extraction", sa.JSON(), nullable=True))
    op.add_column("drafts", sa.Column("extraction_status", sa.String(16), nullable=False, server_default="not_started"))
    op.add_column("drafts", sa.Column("extraction_attempt_id", sa.String(36), nullable=True))
    op.add_column("drafts", sa.Column("extraction_error", sa.String(40), nullable=True))
    op.create_table("extraction_lock", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("revision", sa.Integer(), nullable=False))
    op.execute("INSERT INTO extraction_lock (id, revision) VALUES (1, 0)")
    op.create_table("extraction_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("draft_id", sa.String(36), nullable=False),
        sa.Column("guest_id", sa.String(36), nullable=False),
        sa.Column("started_at", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error", sa.String(40), nullable=True))
    for field in ("draft_id", "guest_id", "started_at"):
        op.create_index(f"ix_extraction_attempts_{field}", "extraction_attempts", [field])


def downgrade():
    op.drop_table("extraction_attempts")
    op.drop_table("extraction_lock")
    for field in ("extraction_error", "extraction_attempt_id", "extraction_status", "extraction"):
        op.drop_column("drafts", field)
