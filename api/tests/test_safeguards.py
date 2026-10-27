import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from src.auth.models import GuestSession
from src.config import settings
from src.main import create_app
from src.safeguards import PublicAccessMiddleware, RateBucket

HEADERS = {"X-Requested-With": "EmailToOrder"}


def restart(app, address="testclient"):
    return TestClient(create_app(db_url=app.state.engine.url.render_as_string(hide_password=False)),
                      client=(address, 50000))


def test_body_limit_before_parsing_including_streamed_and_false_length(app, monkeypatch):
    monkeypatch.setattr(settings, "request_body_limit", 8)
    called = []

    async def parser(scope, receive, send):
        called.append(True)

    async def request(headers, chunks):
        messages = iter({"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
                        for i, chunk in enumerate(chunks))
        sent = []

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        middleware = PublicAccessMiddleware(parser, app.state.sessions)
        await middleware({"type": "http", "path": "/api/orders", "headers": headers,
                          "client": ("testclient", 1)}, receive, send)
        assert sent[0]["status"] == 413

    asyncio.run(request([(b"content-length", b"9")], []))
    asyncio.run(request([], [b"12345", b"6789"]))
    asyncio.run(request([(b"content-length", b"1")], [b"12345", b"6789"]))
    assert called == []


def test_api_rate_survives_cookie_churn_headers_and_restart(client, app, monkeypatch):
    monkeypatch.setattr(settings, "api_address_limit", 2)
    assert client.get("/api/health").status_code == 200
    client.cookies.clear()
    assert client.get("/api/missing", headers={"X-Forwarded-For": "1.2.3.4"}).status_code == 404
    with restart(app) as other:
        response = other.get("/api/health", headers={"X-Forwarded-For": "5.6.7.8"})
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0


def test_guest_churn_and_restart(client, app, monkeypatch):
    monkeypatch.setattr(settings, "guest_address_limit", 2)
    for _ in range(2):
        client.cookies.clear()
        assert client.post("/api/auth/guest", headers=HEADERS).status_code == 200
    # Existing workspace is reusable without consuming a creation slot.
    assert client.post("/api/auth/guest", headers=HEADERS).status_code == 200
    with restart(app) as other:
        assert other.post("/api/auth/guest", headers=HEADERS).status_code == 429
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(GuestSession)) == 2


def test_global_rate_and_bounded_expired_buckets(app, monkeypatch):
    from src.safeguards import take_rate
    from fastapi import HTTPException
    import pytest
    monkeypatch.setattr("src.safeguards.time.time", lambda: 1000)
    with app.state.sessions() as db:
        take_rate(db, "api", "first", 10, 1, 60)
        db.commit()
        with pytest.raises(HTTPException) as error:
            take_rate(db, "api", "second", 10, 1, 60)
        assert error.value.status_code == 429
        assert db.scalar(select(func.count()).select_from(RateBucket)) == 2
    monkeypatch.setattr("src.safeguards.time.time", lambda: 1060)
    with app.state.sessions() as db:
        take_rate(db, "api", "second", 10, 1, 60)
        db.commit()
        assert db.scalar(select(func.count()).select_from(RateBucket)) == 2


def test_workspace_storage_counts_expired_sessions_after_restart(client, app, monkeypatch):
    monkeypatch.setattr(settings, "workspace_limit", 1)
    assert client.post("/api/auth/guest", headers=HEADERS).status_code == 200
    with app.state.sessions() as db:
        db.scalar(select(GuestSession)).expires_at = 0
        db.commit()
    with restart(app) as other:
        assert other.post("/api/auth/guest", headers=HEADERS).status_code == 409


def test_workspace_caps_are_atomic_and_persistent(guest, app, monkeypatch):
    monkeypatch.setattr(settings, "workspace_order_limit", 1)
    monkeypatch.setattr(settings, "workspace_customer_limit", 1)
    monkeypatch.setattr(settings, "workspace_product_limit", 1)
    payloads = [
        ("/api/orders", {"email": "Order please"}),
        ("/api/customers", {"name": "New customer", "email": "new@example.com"}),
        ("/api/catalogue/products", {"sku": "NEW", "name": "New product", "pack_size": 1,
                                     "price": "1.00", "stock_cases": 1}),
    ]
    for path, payload in payloads:
        # Separate clients/connections, same workspace, racing for the last slot.
        def create(_):
            with restart(app) as other:
                other.cookies.update(guest.cookies)
                return other.post(path, json=payload, headers=HEADERS).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(create, range(2))) == [201, 409]
        with restart(app) as other:
            other.cookies.update(guest.cookies)
            assert other.post(path, json=payload, headers=HEADERS).status_code == 409


def test_order_pagination_validation_filter_and_ownership(guest):
    ids = [guest.post("/api/orders", json={"email": str(i)}, headers=HEADERS).json()["id"] for i in range(3)]
    first = guest.get("/api/orders?limit=2").json()
    second = guest.get("/api/orders?limit=2&offset=2").json()
    assert first["total"] == second["total"] == 3
    assert len(first["items"]) == 2
    assert {item["id"] for item in first["items"] + second["items"]} == set(ids)
    assert guest.get("/api/orders?status=confirmed").json() == {"items": [], "total": 0}
    for query in ("limit=51", "limit=0", "offset=-1", "offset=1001", "status=other"):
        assert guest.get(f"/api/orders?{query}").status_code == 422
    guest.cookies.clear()
    guest.post("/api/auth/guest", headers=HEADERS)
    assert guest.get("/api/orders").json() == {"items": [], "total": 0}


def test_concurrent_guest_creation_cannot_exceed_global_storage(app, monkeypatch):
    monkeypatch.setattr(settings, "workspace_limit", 1)

    def create(_):
        with restart(app) as client:
            return client.post("/api/auth/guest", headers=HEADERS).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(create, range(2))) == [200, 409]
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(GuestSession)) == 1


def test_concurrent_api_requests_cannot_exceed_budget(app, monkeypatch):
    monkeypatch.setattr(settings, "api_global_limit", 1)

    def request(_):
        with restart(app) as client:
            return client.get("/api/health").status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(request, range(2))) == [200, 429]


def test_oversized_request_consumes_persistent_api_budget(client, app, monkeypatch):
    monkeypatch.setattr(settings, "api_address_limit", 1)
    response = client.post("/api/orders", content=b"{" * (settings.request_body_limit + 1), headers=HEADERS)
    assert response.status_code == 413
    with restart(app) as other:
        assert other.get("/api/health").status_code == 429


def test_global_guest_rate_survives_address_rotation_and_restart(app, monkeypatch):
    monkeypatch.setattr(settings, "guest_global_limit", 1)
    with restart(app, "192.0.2.1") as first:
        assert first.post("/api/auth/guest", headers=HEADERS).status_code == 200
    with restart(app, "192.0.2.2") as second:
        response = second.post("/api/auth/guest", headers=HEADERS)
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0
    with app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(GuestSession)) == 1
