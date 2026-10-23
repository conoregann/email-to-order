from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from sqlalchemy import inspect
from src.database import Base, make_engine


def test_migration_round_trip_and_model_alignment(app):
    url = app.state.engine.url.render_as_string(hide_password=False)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    engine = make_engine(url)
    with engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    assert "confirmed_orders" in inspect(engine).get_table_names()
    engine.dispose()


def test_legacy_drafts_survive_upgrade(guest, app):
    from test_drafts import create_sample
    from test_confirmation import confirm
    from test_drafts import save
    draft = create_sample(guest)
    ready = save(guest, create_sample(guest), delivery_confirmed=True).json()
    confirmed = confirm(guest, ready).json()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = app.state.engine.url.render_as_string(hide_password=False)
    command.downgrade(config, "0001")
    command.upgrade(config, "head")
    restored = guest.get(f"/api/orders/{draft['id']}").json()
    assert restored["initial_values"] == draft["initial_values"]
    assert restored["values"] == draft["values"]
    assert restored["extraction"] is None
    assert restored["extraction_status"] == "not_started"
    assert guest.get(f"/api/orders/{confirmed['id']}").json()["confirmed"] == confirmed["confirmed"]
