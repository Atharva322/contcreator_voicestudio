from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from app.database import enable_sqlite_foreign_keys
from app.models import CreatorProfile, Draft, ImportedPost, StyleProfile, utc_now

ROOT = Path(__file__).resolve().parents[3]
TMP_ROOT = ROOT / ".test-tmp"


@pytest.fixture()
def workspace_tmp_path() -> Path:
    path = TMP_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def alembic_config(db_path: Path) -> Config:
    config = Config(str(ROOT / "apps" / "api" / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    return config


def upgrade(db_path: Path) -> None:
    command.upgrade(alembic_config(db_path), "head")


def table_columns(db_path: Path, table: str) -> set[str]:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    with engine.connect() as connection:
        return {column["name"] for column in sa.inspect(connection).get_columns(table)}


def test_empty_database_upgrades_to_head(workspace_tmp_path: Path) -> None:
    db_path = workspace_tmp_path / "empty.db"
    upgrade(db_path)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    with engine.connect() as connection:
        inspector = sa.inspect(connection)
        assert "creatorprofile" in inspector.get_table_names()
        assert "include_in_analysis" in table_columns(db_path, "importedpost")
        assert connection.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one() == "20260809_0002"


def test_legacy_database_upgrade_preserves_rows_and_adds_quality_columns(workspace_tmp_path: Path) -> None:
    db_path = workspace_tmp_path / "legacy.db"
    create_legacy_database(db_path)
    upgrade(db_path)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    enable_sqlite_foreign_keys(engine)
    with engine.connect() as connection:
        post = connection.execute(sa.text("SELECT quality_score, quality_labels, include_in_analysis FROM importedpost")).first()
        assert post == (100, "[]", 1)
        assert connection.execute(sa.text("SELECT COUNT(*) FROM creatorprofile")).scalar_one() == 1
        assert connection.execute(sa.text("SELECT COUNT(*) FROM draft")).scalar_one() == 1


def test_upgrade_head_is_idempotent(workspace_tmp_path: Path) -> None:
    db_path = workspace_tmp_path / "idempotent.db"
    upgrade(db_path)
    upgrade(db_path)

    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    with engine.connect() as connection:
        assert connection.execute(sa.text("SELECT COUNT(*) FROM alembic_version")).scalar_one() == 1


def test_legacy_orphan_rows_block_foreign_key_migration(workspace_tmp_path: Path) -> None:
    db_path = workspace_tmp_path / "orphan.db"
    create_legacy_database(db_path, creator_id=999, include_creator=False)

    with pytest.raises(RuntimeError, match="orphan rows"):
        upgrade(db_path)


def test_foreign_keys_reject_orphans_and_cascade_delete(workspace_tmp_path: Path) -> None:
    db_path = workspace_tmp_path / "integrity.db"
    upgrade(db_path)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    enable_sqlite_foreign_keys(engine)

    with Session(engine) as session:
        creator_a = CreatorProfile(name="A")
        creator_b = CreatorProfile(name="B")
        session.add(creator_a)
        session.add(creator_b)
        session.commit()
        session.refresh(creator_a)
        session.refresh(creator_b)

        session.add(ImportedPost(creator_id=creator_a.id or 0, platform="x", text="owned"))
        session.add(ImportedPost(creator_id=creator_b.id or 0, platform="x", text="other"))
        session.commit()

        session.add(ImportedPost(creator_id=9999, platform="x", text="orphan"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        session.delete(creator_a)
        session.commit()

        remaining_posts = session.exec(select(ImportedPost)).all()
        assert [post.text for post in remaining_posts] == ["other"]
        assert session.get(CreatorProfile, creator_b.id) is not None


def test_clear_workspace_preserves_profile_and_unique_style_profile(workspace_tmp_path: Path) -> None:
    db_path = workspace_tmp_path / "workspace.db"
    upgrade(db_path)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    enable_sqlite_foreign_keys(engine)

    with Session(engine) as session:
        creator = CreatorProfile(name="Creator")
        session.add(creator)
        session.commit()
        session.refresh(creator)
        creator_id = creator.id or 0
        session.add(ImportedPost(creator_id=creator_id, platform="x", text="sample"))
        session.add(style_profile(creator_id))
        session.commit()

        session.add(style_profile(creator_id))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        for record in session.exec(select(ImportedPost).where(ImportedPost.creator_id == creator_id)).all():
            session.delete(record)
        for record in session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).all():
            session.delete(record)
        session.commit()

        assert session.get(CreatorProfile, creator_id) is not None
        assert session.exec(select(ImportedPost).where(ImportedPost.creator_id == creator_id)).all() == []
        assert session.exec(select(StyleProfile).where(StyleProfile.creator_id == creator_id)).all() == []


def style_profile(creator_id: int) -> StyleProfile:
    return StyleProfile(
        creator_id=creator_id,
        summary="summary",
        tone="tone",
        hooks="hooks",
        rhythm="rhythm",
        vocabulary="vocabulary",
        emoji_hashtag_habits="emoji",
        cta_habits="cta",
        formatting="formatting",
        avoid_rules="avoid",
        raw_json="{}",
    )


def create_legacy_database(db_path: Path, creator_id: int = 1, include_creator: bool = True) -> None:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    now = utc_now().replace(tzinfo=None)
    metadata = sa.MetaData()
    sa.Table(
        "creatorprofile",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("niche", sa.String(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("goals", sa.String(), nullable=False),
        sa.Column("platforms", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    sa.Table(
        "importedpost",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("external_id", sa.String(), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    sa.Table(
        "draft",
        metadata,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("draft_format", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("cta", sa.String(), nullable=False),
        sa.Column("length", sa.String(), nullable=False),
        sa.Column("creativity", sa.Float(), nullable=False),
        sa.Column("variants_json", sa.String(), nullable=False),
        sa.Column("selected_text", sa.String(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("feedback", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for name in ("styleprofile", "styleguiderevision", "voicesuggestion"):
        SQLModel.metadata.tables[name].to_metadata(metadata)
    metadata.create_all(engine)

    with engine.begin() as connection:
        if include_creator:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO creatorprofile
                    (id, name, niche, audience, goals, platforms, created_at, updated_at)
                    VALUES (:id, 'Legacy', '', '', '', 'x,instagram', :now, :now)
                    """
                ),
                {"id": creator_id, "now": now},
            )
        connection.execute(
            sa.text(
                """
                INSERT INTO importedpost
                (creator_id, platform, text, source, created_at)
                VALUES (:creator_id, 'x', 'legacy sample', 'manual', :now)
                """
            ),
            {"creator_id": creator_id, "now": now},
        )
        connection.execute(
            sa.text(
                """
                INSERT INTO draft
                (creator_id, platform, draft_format, topic, audience, cta, length, creativity, variants_json, created_at, updated_at)
                VALUES (:creator_id, 'x', 'x_post', 'topic', '', '', 'medium', 0.5, '[]', :now, :now)
                """
            ),
            {"creator_id": creator_id, "now": now},
        )
