from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from data.settings import settings

_database_url = make_url(settings.database_url)
if _database_url.drivername == "postgresql":
    _database_url = _database_url.set(drivername="postgresql+psycopg")

engine = create_engine(_database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
