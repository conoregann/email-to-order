"""Persistent public request budgets and storage serialization."""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("public_lock", sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("revision", sa.Integer(), nullable=False))
    op.execute("INSERT INTO public_lock (id, revision) VALUES (1, 0)")
    op.create_table("rate_buckets", sa.Column("key", sa.String(100), primary_key=True),
                    sa.Column("count", sa.Integer(), nullable=False),
                    sa.Column("expires_at", sa.Integer(), nullable=False))
    op.create_index("ix_rate_buckets_expires_at", "rate_buckets", ["expires_at"])


def downgrade():
    op.drop_table("rate_buckets")
    op.drop_table("public_lock")
