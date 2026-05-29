from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from pi5_scada.config import Settings


def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(database_url), autoflush=False, autocommit=False)


def check_database(database_url: str) -> bool:
    engine = make_engine(database_url)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


settings = Settings()
SessionLocal = make_session_factory(settings.database_url)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
