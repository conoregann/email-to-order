"""Repeatable workspace cleanup; run with `python -m src.cleanup` from api/."""
import json
import time
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from src.auth.models import GuestSession
from src.database import database_url, make_engine, session_factory
from src.integrations.usage import lock_usage
from src.orders.models import ExtractionAttempt
from src.safeguards import lock_public


def cleanup(db: Session, now: int) -> dict[str, int]:
    """Caller commits; all deletions and quota locks share one transaction."""
    lock_public(db)
    lock_usage(db)
    guests = db.execute(delete(GuestSession).where(GuestSession.expires_at <= now))
    # Keep active-workspace attempts for retry idempotency. Orphaned attempts
    # must outlive BOTH quota windows and their provider timeout, regardless of status.
    attempts = db.execute(delete(ExtractionAttempt).where(
        ~ExtractionAttempt.guest_id.in_(select(GuestSession.id)),
        ExtractionAttempt.started_at <= now - 86400,
        ExtractionAttempt.started_at < now - now % 86400,
        ExtractionAttempt.expires_at <= now,
    ))
    return {"workspaces_deleted": guests.rowcount, "usage_records_deleted": attempts.rowcount}


def main() -> None:
    engine = make_engine(database_url())
    try:
        with session_factory(engine).begin() as db:
            counts = cleanup(db, int(time.time()))
        print(json.dumps(counts))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
