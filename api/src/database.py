from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from fastapi import Request
from src.config import ROOT, settings

class Base(DeclarativeBase):
    pass


def database_url(value: str | None = None) -> str:
    url = value or settings.database_url or f"sqlite:///{ROOT / '.local' / 'orders.db'}"
    if url.startswith(("postgres://", "postgresql://")):
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    return url


def make_engine(url: str):
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        if parsed.database and parsed.database != ":memory:":
            Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})
        @event.listens_for(engine, "connect")
        def sqlite_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
        return engine
    return create_engine(url, pool_pre_ping=True)


def get_db(request: Request):
    with request.app.state.sessions() as db:
        yield db


def session_factory(engine):
    return sessionmaker(engine, expire_on_commit=False)
