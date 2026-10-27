from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4
import pytest
from sqlalchemy import select
from src.auth.models import GuestSession
from src.catalogue.models import WorkspaceProduct
from src.cleanup import cleanup
from src.config import settings
from src.customers.models import WorkspaceCustomer
from src.integrations.gemini import ExtractionError
from src.integrations.usage import lock_usage, reserve
from src.orders.models import ConfirmedOrder, Draft, DraftLine, ExtractionAttempt
from src.safeguards import RateBucket
from test_confirmation import confirm, ready
from test_customers import create_customer
from test_drafts import create_sample
from test_products import create_product


def attempt(db, guest_id, started_at, status="failed", expires_at=None):
    record = ExtractionAttempt(id=str(uuid4()), guest_id=guest_id, draft_id=str(uuid4()),
                               started_at=started_at, expires_at=expires_at or started_at + 45,
                               status=status)
    db.add(record)
    return record.id


def test_cleanup_cascades_preserves_active_data_and_repeats(guest, app):
    create_sample(guest)
    assert confirm(guest, ready(guest)).status_code == 200
    assert create_customer(guest).status_code == 201
    assert create_product(guest).status_code == 201
    now = int(time.time())
    with app.state.sessions.begin() as db:
        owner = db.scalar(select(GuestSession))
        owner.expires_at = now  # Same boundary as authentication's expires_at > now.
        owner_id = owner.id
        db.add(GuestSession(id="active", token_hash="active", expires_at=now + 1))
        db.flush()
        db.add(Draft(id="active-draft", guest_id="active", original_email="keep", initial_values={},
                     values={}, source="manual", created_at=now, updated_at=now))
        db.flush()
        db.add(DraftLine(id="active-line", draft_id="active-draft", position=0, values={}))
        db.add(ConfirmedOrder(id="active-order", draft_id="active-draft", guest_id="active",
                              number="KEEP", snapshot={}, confirmed_at=now))
        db.add(WorkspaceCustomer(id="active-customer", guest_id="active", name="Keep", email="a@b.test"))
        db.add(WorkspaceProduct(id="active-product", guest_id="active", sku="KEEP", name="Keep",
                                pack_size=1, price=1, stock_cases=1))
        retained_usage = attempt(db, owner_id, now - 1)
        # Even old attempts in an active workspace retain their retry identity.
        active_usage = attempt(db, "active", now - 172800)
        db.add(RateBucket(key="cleanup-test", count=5, expires_at=now + 3600))
    with app.state.sessions.begin() as db:
        assert cleanup(db, now) == {"workspaces_deleted": 1, "usage_records_deleted": 0}
    with app.state.sessions.begin() as db:
        assert list(db.scalars(select(GuestSession.id))) == ["active"]
        assert list(db.scalars(select(Draft.id))) == ["active-draft"]
        assert list(db.scalars(select(DraftLine.id))) == ["active-line"]
        assert list(db.scalars(select(ConfirmedOrder.id))) == ["active-order"]
        assert list(db.scalars(select(WorkspaceCustomer.id))) == ["active-customer"]
        assert list(db.scalars(select(WorkspaceProduct.id))) == ["active-product"]
        assert set(db.scalars(select(ExtractionAttempt.id))) == {retained_usage, active_usage}
        assert db.get(RateBucket, "cleanup-test").count == 5
        assert cleanup(db, now) == {"workspaces_deleted": 0, "usage_records_deleted": 0}


@pytest.mark.parametrize("status", ["running", "failed", "succeeded"])
def test_cleanup_retains_usage_until_rolling_window_ends(app, status):
    midnight = 10 * 86400
    started = midnight - 1
    with app.state.sessions.begin() as db:
        record_id = attempt(db, "deleted-guest", started, status)
    with app.state.sessions.begin() as db:
        # Daily window ended, but rolling guest allowance is still consumed.
        assert cleanup(db, midnight)["usage_records_deleted"] == 0
        assert cleanup(db, started + 86400 - 1)["usage_records_deleted"] == 0
    with app.state.sessions.begin() as db:
        assert cleanup(db, started + 86400)["usage_records_deleted"] == 1
        assert db.get(ExtractionAttempt, record_id) is None


def test_cleanup_cannot_refund_daily_or_guest_allowance(app, monkeypatch):
    now = 10 * 86400 + 100
    monkeypatch.setattr(settings, "extraction_daily_limit", 1)
    monkeypatch.setattr(settings, "extraction_guest_limit", 1)
    with app.state.sessions.begin() as db:
        db.add(GuestSession(id="expired", token_hash="expired", expires_at=now))
        attempt(db, "expired", now - 1)
    with app.state.sessions.begin() as db:
        cleanup(db, now)
    for owner, code in [("expired", "guest_limit"), ("replacement", "daily_limit")]:
        with app.state.sessions() as db:
            lock_usage(db)
            with pytest.raises(ExtractionError) as error:
                reserve(db, owner, "draft", str(uuid4()), now)
            assert error.value.code == code
            db.rollback()
    # Across UTC midnight the daily budget resets naturally, but the guest's
    # rolling budget must survive cleanup until 24 hours have elapsed.
    tomorrow = 11 * 86400
    with app.state.sessions.begin() as db:
        cleanup(db, tomorrow)
        with pytest.raises(ExtractionError) as error:
            reserve(db, "expired", "draft", str(uuid4()), tomorrow)
        assert error.value.code == "guest_limit"
    with app.state.sessions.begin() as db:
        cleanup(db, now + 86400)
        reserve(db, "expired", "draft", str(uuid4()), now + 86400)


def test_cleanup_rolls_back_atomically(app):
    with app.state.sessions.begin() as db:
        db.add(GuestSession(id="expired", token_hash="expired", expires_at=0))
        usage_id = attempt(db, "expired", 0)
    with app.state.sessions() as db:
        assert cleanup(db, 172800) == {"workspaces_deleted": 1, "usage_records_deleted": 1}
        db.rollback()
    with app.state.sessions() as db:
        assert db.get(GuestSession, "expired") is not None
        assert db.get(ExtractionAttempt, usage_id) is not None


def test_overlapping_cleanup_and_reservations_preserve_global_cap(app, monkeypatch):
    now = 10 * 86400 + 100
    monkeypatch.setattr(settings, "extraction_daily_limit", 3)
    with app.state.sessions.begin() as db:
        db.add(GuestSession(id="expired", token_hash="expired", expires_at=now))
        attempt(db, "expired", now - 1)

    def run(index):
        with app.state.sessions.begin() as db:
            if index % 2 == 0:
                cleanup(db, now)
                return 0
            lock_usage(db)
            try:
                reserve(db, str(index), "draft", str(uuid4()), now)
                return 1
            except ExtractionError as error:
                assert error.code == "daily_limit"
                return 0

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(run, range(16))) == 2
    with app.state.sessions() as db:
        assert db.get(GuestSession, "expired") is None
        assert len(list(db.scalars(select(ExtractionAttempt)))) == 3


def test_cleanup_command_uses_configured_database_and_repeats(app):
    with app.state.sessions.begin() as db:
        db.add(GuestSession(id="expired", token_hash="expired", expires_at=0))
        attempt(db, "expired", 0)
    env = {**os.environ, "DATABASE_URL": app.state.engine.url.render_as_string(hide_password=False)}
    for count in (1, 0):
        result = subprocess.run([sys.executable, "-m", "src.cleanup"],
                                cwd=Path(__file__).resolve().parents[1], env=env,
                                capture_output=True, text=True, check=True)
        assert json.loads(result.stdout) == {"workspaces_deleted": count, "usage_records_deleted": count}
