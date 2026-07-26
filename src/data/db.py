from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from data.settings import settings

_database_url = make_url(settings.database_url)
if _database_url.drivername == "postgresql":
    _database_url = _database_url.set(drivername="postgresql+psycopg")

# prepare_threshold=None desliga prepared statements do lado do psycopg3 — o
# Supabase roda em modo "Transaction pooler" (PgBouncer), que não garante a
# mesma conexão física entre execuções; sem isso, a segunda vez que uma query
# repetida roda (ex: o SELECT por pncp_id dentro do loop de persistir_resultados
# da Prospecção) quebra com "DuplicatePreparedStatement".
engine = create_engine(_database_url, connect_args={"prepare_threshold": None})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
