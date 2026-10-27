"""Persistent public quotas; all checks and writes share a database row lock."""
import hashlib
import time
from fastapi import HTTPException
from sqlalchemy import String, delete, func, select, update
from sqlalchemy.orm import Mapped, mapped_column
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from src.config import settings
from src.database import Base


class PublicLock(Base):
    __tablename__ = "public_lock"
    id: Mapped[int] = mapped_column(primary_key=True)
    revision: Mapped[int] = mapped_column(default=0)


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int]
    expires_at: Mapped[int] = mapped_column(index=True)


def lock_public(db):
    db.execute(update(PublicLock).where(PublicLock.id == 1).values(revision=PublicLock.revision + 1))


def check_capacity(db, model, limit, label, guest_id=None):
    lock_public(db)
    query = select(func.count()).select_from(model)
    if guest_id is not None:
        query = query.where(model.guest_id == guest_id)
    if db.scalar(query) >= limit:
        raise HTTPException(409, f"{label} limit reached ({limit}).")


def take_rate(db, category, address, per_address, global_limit, seconds):
    lock_public(db)
    now = int(time.time())
    db.execute(delete(RateBucket).where(RateBucket.expires_at <= now))
    identity = hashlib.sha256(address.encode()).hexdigest()
    for key, limit in ((f"{category}:global", global_limit), (f"{category}:{identity}", per_address)):
        bucket = db.get(RateBucket, key)
        if bucket and bucket.count >= limit:
            retry = bucket.expires_at - now
            # Retain earlier global consumption even when the address is blocked.
            db.commit()
            raise HTTPException(429, "Too many requests. Please try again later.", headers={"Retry-After": str(retry)})
        if bucket:
            bucket.count += 1
        else:
            db.add(RateBucket(key=key, count=1, expires_at=now + seconds))
        db.flush()


class PublicAccessMiddleware:
    def __init__(self, app, sessions):
        self.app = app
        self.sessions = sessions

    def rate_request(self, address):
        with self.sessions() as db:
            take_rate(db, "api", address, settings.api_address_limit, settings.api_global_limit, 60)
            db.commit()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not (scope["path"] == "/api" or scope["path"].startswith("/api/")):
            return await self.app(scope, receive, send)
        try:
            # Never trust caller-supplied forwarding headers. Uvicorn must also be
            # configured to trust only the deployment's actual reverse proxy.
            address = scope.get("client", ("unknown", 0))[0]
            await run_in_threadpool(self.rate_request, address)
            for name, value in scope["headers"]:
                if name.lower() == b"content-length":
                    try:
                        length = int(value)
                    except ValueError:
                        raise HTTPException(400, "Invalid Content-Length") from None
                    if length < 0:
                        raise HTTPException(400, "Invalid Content-Length")
                    if length > settings.request_body_limit:
                        raise HTTPException(413, "Request body too large.")
            body = bytearray()
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                if len(body) + len(chunk) > settings.request_body_limit:
                    raise HTTPException(413, "Request body too large.")
                body.extend(chunk)
                if not message.get("more_body", False):
                    break
        except HTTPException as error:
            return await JSONResponse({"detail": error.detail}, status_code=error.status_code,
                                      headers=error.headers)(scope, receive, send)

        async def bounded_receive():
            nonlocal body
            if body is not None:
                message = {"type": "http.request", "body": bytes(body), "more_body": False}
                body = None
                return message
            return await receive()

        await self.app(scope, bounded_receive, send)
