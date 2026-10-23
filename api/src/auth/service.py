import hashlib
import secrets
import time
from uuid import uuid4
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.auth.models import GuestSession
from src.database import get_db

COOKIE = "eto_guest"
SESSION_SECONDS = 24 * 60 * 60


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def find_guest(request: Request, db: Session) -> GuestSession | None:
    token = request.cookies.get(COOKIE, "")
    if not token or len(token) > 100:
        return None
    return db.scalar(select(GuestSession).where(
        GuestSession.token_hash == token_hash(token), GuestSession.expires_at > int(time.time())
    ))


def current_guest(request: Request, db: Session = Depends(get_db)) -> GuestSession:
    guest = find_guest(request, db)
    if guest is None:
        raise HTTPException(401, "Guest workspace expired or missing. Start a new workspace from Orders.")
    return guest


def require_browser_header(request: Request):
    if request.headers.get("X-Requested-With") != "EmailToOrder":
        raise HTTPException(403, "Missing request verification header")


def new_guest(db: Session) -> tuple[GuestSession, str]:
    token = secrets.token_urlsafe(32)
    guest = GuestSession(id=str(uuid4()), token_hash=token_hash(token), expires_at=int(time.time()) + SESSION_SECONDS)
    db.add(guest)
    db.commit()
    return guest, token
