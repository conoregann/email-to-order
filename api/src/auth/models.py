from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class GuestSession(Base):
    __tablename__ = "guest_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[int] = mapped_column(index=True)
