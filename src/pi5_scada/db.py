from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pi5_scada.config import Settings


def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(database_url), autoflush=False, autocommit=False)


settings = Settings()
SessionLocal = make_session_factory(settings.database_url)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
