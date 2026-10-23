from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


class WorkspaceProduct(Base):
    __tablename__ = "workspace_products"
    __table_args__ = (UniqueConstraint("guest_id", "sku"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(300))
    pack_size: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_cases: Mapped[int]
