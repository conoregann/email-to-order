from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config import settings

class Base(DeclarativeBase):
    pass

# Do not connect during imports or require database credentials for the scaffold.
engine = create_engine(settings.database_url) if settings.database_url else None
SessionLocal = sessionmaker(bind=engine) if engine else None
