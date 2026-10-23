import time
from sqlalchemy import select
from src.auth.models import GuestSession


def test_guest_cookie_reuse_and_expiry(client, app):
    headers = {"X-Requested-With": "EmailToOrder"}
    assert client.post("/api/auth/guest").status_code == 403
    first = client.post("/api/auth/guest", headers=headers)
    cookie = client.cookies.get("eto_guest")
    assert "HttpOnly" in first.headers["set-cookie"]
    assert "SameSite=strict" in first.headers["set-cookie"]
    assert client.post("/api/auth/guest", headers=headers).json() == first.json()
    assert client.cookies.get("eto_guest") == cookie
    with app.state.sessions() as db:
        session = db.scalar(select(GuestSession))
        assert session.token_hash != cookie
        session.expires_at = int(time.time()) - 1
        db.commit()
    client.post("/api/auth/guest", headers=headers)
    assert client.cookies.get("eto_guest") != cookie
