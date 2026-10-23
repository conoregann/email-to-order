from sqlalchemy import ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database import Base

class Draft(Base):
    __tablename__ = "drafts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True)
    original_email: Mapped[str] = mapped_column(Text)
    initial_values: Mapped[dict] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(40))
    values: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    created_at: Mapped[int]
    updated_at: Mapped[int]
    lines: Mapped[list["DraftLine"]] = relationship(cascade="all, delete-orphan", order_by="DraftLine.position")

class DraftLine(Base):
    __tablename__ = "draft_lines"
    __table_args__ = (UniqueConstraint("draft_id", "position"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    values: Mapped[dict] = mapped_column(JSON)

class ConfirmedOrder(Base):
    __tablename__ = "confirmed_orders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.id", ondelete="CASCADE"), unique=True)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True)
    number: Mapped[str] = mapped_column(String(40), unique=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    confirmed_at: Mapped[int]
