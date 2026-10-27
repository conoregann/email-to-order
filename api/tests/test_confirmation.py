from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from src.orders.models import ConfirmedOrder
from src.catalogue.service import PRODUCTS
from test_drafts import HEADERS, create_sample, save


def confirm(guest, draft):
    return guest.post(f"/api/orders/{draft['id']}/confirm", json={"version": draft["version"]}, headers=HEADERS)


def ready(guest, sample="straightforward"):
    draft = create_sample(guest, sample)
    return save(guest, draft, delivery_confirmed=True).json()


def test_confirmation_rechecks_and_retries_without_duplicates(guest, app):
    blocked = create_sample(guest)
    assert confirm(guest, blocked).status_code == 422
    draft = save(guest, blocked, delivery_confirmed=True).json()
    assert confirm(guest, blocked).status_code == 409
    first = confirm(guest, draft)
    assert first.status_code == 200, first.text
    order = first.json()
    assert order["status"] == "confirmed"
    assert order["confirmed"]["validation"]["total"] == "27.60"
    assert "SIMULATED" in order["confirmed"]["confirmation_preview"]
    assert confirm(guest, draft).json()["confirmed"] == order["confirmed"]
    assert save(guest, order).status_code == 409
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ConfirmedOrder)) == 1
    assert guest.get("/api/orders").json()["items"][0]["confirmed"] == order["confirmed"]


def test_concurrent_confirmations_have_one_order(guest, app):
    draft = ready(guest)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: confirm(guest, draft), range(8)))
    assert all(result.status_code == 200 for result in results), [r.text for r in results]
    assert len({r.json()["confirmed"]["number"] for r in results}) == 1
    assert all(result.json()["status"] == "confirmed" for result in results)
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ConfirmedOrder)) == 1


def test_confirmation_ownership_and_required_header(guest, app):
    draft = ready(guest)
    assert guest.post(f"/api/orders/{draft['id']}/confirm", json={"version": draft["version"]}).status_code == 403
    with TestClient(app) as stranger:
        stranger.post("/api/auth/guest", headers=HEADERS)
        assert confirm(stranger, draft).status_code == 404
    confirm(guest, draft)
    with TestClient(app) as stranger:
        stranger.post("/api/auth/guest", headers=HEADERS)
        assert stranger.get(f"/api/orders/{draft['id']}").status_code == 404
        assert confirm(stranger, draft).status_code == 404


def test_confirm_revalidates_stock_and_freezes_snapshot(guest, monkeypatch):
    draft = ready(guest)
    changed = tuple(product.model_copy(update={"stock_cases": 0}) for product in PRODUCTS)
    monkeypatch.setattr("src.catalogue.service.PRODUCTS", changed)
    assert confirm(guest, draft).status_code == 422
    monkeypatch.setattr("src.catalogue.service.PRODUCTS", PRODUCTS)
    order = confirm(guest, draft).json()["confirmed"]
    monkeypatch.setattr("src.catalogue.service.PRODUCTS", changed)
    assert guest.get(f"/api/orders/{draft['id']}").json()["confirmed"] == order


def test_seeded_issues_can_be_corrected_and_confirmed(guest):
    for sample in ("ambiguous", "missing-address", "quantity", "stock"):
        draft = create_sample(guest, sample)
        assert confirm(guest, draft).status_code == 422
        values = draft["values"]
        values["delivery_address"] = values["delivery_address"] or "12 Quay Street, Demo Town, Ireland"
        values["delivery_confirmed"] = True
        if sample == "ambiguous":
            values["lines"][0].update(sku="OAT-1L-06", match_confirmed=True)
        elif sample == "quantity":
            values["lines"][0]["quantity"] = "100"
        elif sample == "stock":
            values["lines"][0]["quantity"] = "8"
        updated = save(guest, draft, **values).json()
        result = confirm(guest, updated)
        assert result.status_code == 200, result.text
        assert result.json()["confirmed"]["initial_values"] == draft["initial_values"]
