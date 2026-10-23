from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from sqlalchemy import func, select
from src.config import settings
from src.integrations.gemini import ExtractionError
from src.integrations.usage import lock_usage, reserve
from src.orders.models import ExtractionAttempt


@pytest.mark.parametrize("same_guest,expected", [(True, 5), (False, 7)])
def test_concurrent_durable_caps(app, monkeypatch, same_guest, expected):
    monkeypatch.setattr(settings, "extraction_daily_limit", 7)
    def attempt(index):
        with app.state.sessions() as db:
            try:
                lock_usage(db)
                reserve(db, "guest" if same_guest else str(index), "draft", str(uuid4()), 86401)
                db.commit()
                return True
            except ExtractionError:
                db.rollback()
                return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(12))) == expected
    # A new session sees all committed reservations, even failed provider attempts.
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ExtractionAttempt)) == expected
        lock_usage(db)
        reserve(db, "guest", "draft", str(uuid4()), 86401 + 86400)
        db.commit()
