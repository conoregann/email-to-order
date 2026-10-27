import time
from fastapi.testclient import TestClient
from sqlalchemy import select
from src.auth.models import GuestSession
from src.auth.service import token_hash
from src.orders.service import SAMPLES

HEADERS = {"X-Requested-With": "EmailToOrder"}


def create_sample(guest, sample_id="straightforward"):
    sample = next(sample for sample in SAMPLES if sample.id == sample_id)
    response = guest.post("/api/orders", json={"email": sample.body, "sample_id": sample_id}, headers=HEADERS)
    assert response.status_code == 201, response.text
    return response.json()


def save(guest, draft, **values):
    payload = {**draft["values"], **values, "version": draft["version"]}
    return guest.put(f"/api/orders/{draft['id']}", json=payload, headers=HEADERS)


def test_manual_draft_preserves_email_and_initial_values(guest):
    draft = guest.post("/api/orders", json={"email": "  <script>alert(1)</script> customer text\n "}, headers=HEADERS).json()
    assert draft["original_email"] == "  <script>alert(1)</script> customer text\n "
    assert draft["values"]["customer_id"] is None
    assert draft["values"]["lines"] == []
    assert not draft["validation"]["can_confirm"]
    edited = save(guest, draft, customer_id="harbour-cafe", delivery_address="Custom warehouse").json()
    assert edited["version"] == 2
    assert edited["original_email"] == draft["original_email"]
    assert edited["initial_values"] == draft["initial_values"]
    assert edited["values"]["delivery_address"] == "Custom warehouse"
    assert save(guest, draft).status_code == 409


def test_ownership_on_every_draft_operation(guest, app):
    draft = create_sample(guest)
    with TestClient(app) as stranger:
        assert stranger.get("/api/orders").status_code == 401
        stranger.post("/api/auth/guest", headers=HEADERS)
        assert stranger.get("/api/orders").json()["items"] == []
        assert stranger.get(f"/api/orders/{draft['id']}").status_code == 404
        assert save(stranger, draft).status_code == 404
    with app.state.sessions() as db:
        session = db.scalar(select(GuestSession).where(GuestSession.token_hash == token_hash(guest.cookies.get("eto_guest"))))
        session.expires_at = int(time.time()) - 1
        db.commit()
    assert guest.get(f"/api/orders/{draft['id']}").status_code == 401


def test_samples_require_exact_original_email(guest):
    assert guest.post("/api/orders", json={"email": "edited", "sample_id": "straightforward"}, headers=HEADERS).status_code == 422
    assert guest.post("/api/orders", json={"email": " \n "}, headers=HEADERS).status_code == 422
    assert guest.post("/api/orders", json={"email": "x" * 20001}, headers=HEADERS).status_code == 422


def test_backend_prices_and_input_limits(guest):
    draft = create_sample(guest)
    draft["values"]["lines"][0]["price"] = "0.01"
    assert save(guest, draft).status_code == 422


def test_persistence_across_application_instances(guest, app):
    from src.main import create_app
    draft = create_sample(guest)
    restarted = create_app(db_url=app.state.engine.url.render_as_string(hide_password=False))
    with TestClient(restarted) as client:
        client.cookies.set("eto_guest", guest.cookies.get("eto_guest"), path="/api")
        response = client.get(f"/api/orders/{draft['id']}")
        assert response.status_code == 200
        assert response.json()["initial_values"] == draft["initial_values"]
    restarted.state.engine.dispose()


def test_save_updates_and_removes_multiple_lines(guest):
    draft = create_sample(guest)
    lines = draft["values"]["lines"]
    first = save(guest, draft, lines=[*lines, *lines]).json()
    assert len(first["values"]["lines"]) == 2
    second = save(guest, first, lines=[lines[0]]).json()
    assert len(second["values"]["lines"]) == 1
    assert save(guest, second, lines=[]).json()["validation"]["can_confirm"] is False
