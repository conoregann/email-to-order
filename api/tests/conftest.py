from pathlib import Path
import os
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from src.main import create_app

@pytest.fixture
def app(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    admin = None
    if os.environ.get("TEST_DATABASE_URL"):
        admin = create_engine(os.environ["TEST_DATABASE_URL"])
        schema = "test_" + uuid4().hex
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        url = make_url(os.environ["TEST_DATABASE_URL"]).update_query_dict({"options": f"-csearch_path={schema}"}).render_as_string(hide_password=False)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    application = create_app(db_url=url)
    yield application
    application.state.engine.dispose()
    if admin:
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()

@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client

@pytest.fixture
def guest(client):
    assert client.post("/api/auth/guest", headers={"X-Requested-With": "EmailToOrder"}).status_code == 200
    return client
