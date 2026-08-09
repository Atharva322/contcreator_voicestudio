from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260809_0002"
down_revision = "20260809_0001"
branch_labels = None
depends_on = None

OWNER_TABLES = (
    "importedpost",
    "styleprofile",
    "styleguiderevision",
    "voicesuggestion",
    "draft",
)


def columns_for(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def assert_no_orphans() -> None:
    bind = op.get_bind()
    for table_name in OWNER_TABLES:
        count = bind.execute(
            sa.text(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                LEFT JOIN creatorprofile ON {table_name}.creator_id = creatorprofile.id
                WHERE creatorprofile.id IS NULL
                """
            )
        ).scalar_one()
        if count:
            raise RuntimeError(f"Cannot add creator foreign key: {table_name} has {count} orphan rows")


def add_quality_columns() -> None:
    existing = columns_for("importedpost")
    with op.batch_alter_table("importedpost", recreate="auto") as batch:
        if "quality_score" not in existing:
            batch.add_column(sa.Column("quality_score", sa.Integer(), nullable=False, server_default="100"))
        if "quality_labels" not in existing:
            batch.add_column(sa.Column("quality_labels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        if "quality_warnings" not in existing:
            batch.add_column(sa.Column("quality_warnings", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        if "include_in_analysis" not in existing:
            batch.add_column(sa.Column("include_in_analysis", sa.Boolean(), nullable=False, server_default=sa.text("1")))


def rebuild_with_foreign_key(table_name: str, constraint_name: str) -> None:
    with op.batch_alter_table(table_name, recreate="always") as batch:
        batch.create_foreign_key(
            constraint_name,
            "creatorprofile",
            ["creator_id"],
            ["id"],
            ondelete="CASCADE",
        )


def upgrade() -> None:
    add_quality_columns()
    assert_no_orphans()
    rebuild_with_foreign_key("importedpost", "fk_importedpost_creator_id_creatorprofile")
    rebuild_with_foreign_key("styleprofile", "fk_styleprofile_creator_id_creatorprofile")
    rebuild_with_foreign_key("styleguiderevision", "fk_styleguiderevision_creator_id_creatorprofile")
    rebuild_with_foreign_key("voicesuggestion", "fk_voicesuggestion_creator_id_creatorprofile")
    rebuild_with_foreign_key("draft", "fk_draft_creator_id_creatorprofile")


def downgrade() -> None:
    # Local migrations are forward-only for data integrity. Keep the schema usable
    # rather than dropping creator-owned data or quality metadata.
    pass
