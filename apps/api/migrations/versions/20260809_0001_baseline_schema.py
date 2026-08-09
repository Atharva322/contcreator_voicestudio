from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260809_0001"
down_revision = None
branch_labels = None
depends_on = None


def has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if not has_table("creatorprofile"):
        op.create_table(
            "creatorprofile",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("niche", sa.String(), nullable=False),
            sa.Column("audience", sa.String(), nullable=False),
            sa.Column("goals", sa.String(), nullable=False),
            sa.Column("platforms", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if not has_table("importedpost"):
        op.create_table(
            "importedpost",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("creator_id", sa.Integer(), nullable=False),
            sa.Column("platform", sa.String(), nullable=False),
            sa.Column("text", sa.String(), nullable=False),
            sa.Column("source", sa.String(), nullable=False),
            sa.Column("source_url", sa.String(), nullable=True),
            sa.Column("external_id", sa.String(), nullable=True),
            sa.Column("posted_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_importedpost_creator_id", "importedpost", ["creator_id"])
        op.create_index("ix_importedpost_external_id", "importedpost", ["external_id"])

    if not has_table("styleprofile"):
        op.create_table(
            "styleprofile",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("creator_id", sa.Integer(), nullable=False),
            sa.Column("summary", sa.String(), nullable=False),
            sa.Column("tone", sa.String(), nullable=False),
            sa.Column("hooks", sa.String(), nullable=False),
            sa.Column("rhythm", sa.String(), nullable=False),
            sa.Column("vocabulary", sa.String(), nullable=False),
            sa.Column("emoji_hashtag_habits", sa.String(), nullable=False),
            sa.Column("cta_habits", sa.String(), nullable=False),
            sa.Column("formatting", sa.String(), nullable=False),
            sa.Column("avoid_rules", sa.String(), nullable=False),
            sa.Column("raw_json", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_styleprofile_creator_id", "styleprofile", ["creator_id"], unique=True)

    if not has_table("styleguiderevision"):
        op.create_table(
            "styleguiderevision",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("creator_id", sa.Integer(), nullable=False),
            sa.Column("summary", sa.String(), nullable=False),
            sa.Column("tone", sa.String(), nullable=False),
            sa.Column("hooks", sa.String(), nullable=False),
            sa.Column("rhythm", sa.String(), nullable=False),
            sa.Column("vocabulary", sa.String(), nullable=False),
            sa.Column("emoji_hashtag_habits", sa.String(), nullable=False),
            sa.Column("cta_habits", sa.String(), nullable=False),
            sa.Column("formatting", sa.String(), nullable=False),
            sa.Column("avoid_rules", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_styleguiderevision_creator_id", "styleguiderevision", ["creator_id"])

    if not has_table("voicesuggestion"):
        op.create_table(
            "voicesuggestion",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("creator_id", sa.Integer(), nullable=False),
            sa.Column("source_draft_id", sa.Integer(), nullable=True),
            sa.Column("target_field", sa.String(), nullable=False),
            sa.Column("suggestion", sa.String(), nullable=False),
            sa.Column("rationale", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_voicesuggestion_creator_id", "voicesuggestion", ["creator_id"])
        op.create_index("ix_voicesuggestion_source_draft_id", "voicesuggestion", ["source_draft_id"])
        op.create_index("ix_voicesuggestion_status", "voicesuggestion", ["status"])

    if not has_table("draft"):
        op.create_table(
            "draft",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
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
        op.create_index("ix_draft_creator_id", "draft", ["creator_id"])


def downgrade() -> None:
    for table_name in (
        "draft",
        "voicesuggestion",
        "styleguiderevision",
        "styleprofile",
        "importedpost",
        "creatorprofile",
    ):
        if has_table(table_name):
            op.drop_table(table_name)
