from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from src.main import create_app

@pytest.fixture
def app(tmp_path):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    application = create_app(db_url=url)
    yield application
    application.state.engine.dispose()

@pytest.fixture
def client(app):
    with TestClient(app) as client:
        yield client

@pytest.fixture
def guest(client):
    assert client.post("/api/auth/guest", headers={"X-Requested-With": "EmailToOrder"}).status_code == 200
    return client
