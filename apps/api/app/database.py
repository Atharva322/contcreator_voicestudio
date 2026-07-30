from collections.abc import Generator

from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_kwargs = {"connect_args": connect_args}
if settings.database_url in {"sqlite://", "sqlite:///:memory:"}:
    engine_kwargs["poolclass"] = StaticPool
engine = create_engine(settings.database_url, **engine_kwargs)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    ensure_imported_post_quality_columns()


def ensure_imported_post_quality_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    columns = {
        "quality_score": "INTEGER NOT NULL DEFAULT 100",
        "quality_labels": "JSON NOT NULL DEFAULT '[]'",
        "quality_warnings": "JSON NOT NULL DEFAULT '[]'",
        "include_in_analysis": "BOOLEAN NOT NULL DEFAULT 1",
    }
    with engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(importedpost)")).fetchall()
        }
        for name, definition in columns.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE importedpost ADD COLUMN {name} {definition}"))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
