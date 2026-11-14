from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def build_database(database_url: str | None = None):
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./aegis.db")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    if url.startswith("sqlite:///") and ":memory:" not in url:
        db_path = url.removeprefix("sqlite:///").split("?", 1)[0]
        Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    engine_kwargs = {"connect_args": connect_args, "pool_pre_ping": True}
    if url in {"sqlite://", "sqlite:///:memory:"}:
        engine_kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **engine_kwargs)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return engine, factory


def get_session(factory: sessionmaker) -> Generator[Session, None, None]:
    db = factory()
    try:
        yield db
    finally:
        db.close()
