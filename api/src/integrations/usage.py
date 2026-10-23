"""Short transactions serialize reservations on both SQLite and PostgreSQL."""
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from src.config import settings
from src.integrations.gemini import ExtractionError
from src.orders.models import ExtractionAttempt, ExtractionLock


def lock_usage(db: Session) -> None:
    # The migration seeds this singleton. UPDATE holds its row/write lock until commit.
    db.execute(update(ExtractionLock).where(ExtractionLock.id == 1).values(revision=ExtractionLock.revision + 1))


def reserve(db: Session, guest_id: str, draft_id: str, attempt_id: str, now: int) -> ExtractionAttempt:
    """Caller holds lock_usage; reservation commits with the draft's running state."""
    guest_count = db.scalar(select(func.count()).select_from(ExtractionAttempt).where(
        ExtractionAttempt.guest_id == guest_id, ExtractionAttempt.started_at > now - 86400))
    daily_count = db.scalar(select(func.count()).select_from(ExtractionAttempt).where(
        ExtractionAttempt.started_at >= now - now % 86400))
    if guest_count >= settings.extraction_guest_limit:
        raise ExtractionError("guest_limit")
    if daily_count >= settings.extraction_daily_limit:
        raise ExtractionError("daily_limit")
    attempt = ExtractionAttempt(id=attempt_id, draft_id=draft_id, guest_id=guest_id, started_at=now,
                                expires_at=now + settings.extraction_timeout_seconds + 15, status="running")
    db.add(attempt)
    return attempt
