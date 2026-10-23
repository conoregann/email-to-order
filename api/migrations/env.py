from alembic import context
from src.database import Base, database_url, make_engine
from src.auth.models import GuestSession  # noqa: F401
from src.customers.models import WorkspaceCustomer  # noqa: F401
from src.catalogue.models import WorkspaceProduct  # noqa: F401
from src.orders.models import Draft, DraftLine, ConfirmedOrder  # noqa: F401

config = context.config
url = config.attributes.get("database_url") or database_url()

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
